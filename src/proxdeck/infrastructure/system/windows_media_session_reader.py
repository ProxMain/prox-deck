from __future__ import annotations

import json
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MediaSessionSnapshot:
    title: str
    artist: str
    source_app: str
    position_seconds: float | None
    duration_seconds: float | None
    audio_level: float | None
    is_playing: bool | None
    is_available: bool


class CommandRunner(Protocol):
    def __call__(self, command: list[str], timeout: float) -> subprocess.CompletedProcess[str]: ...


class AudioSessionReader(Protocol):
    def __call__(self) -> MediaSessionSnapshot: ...


POWERSHELL_MEDIA_SESSION_SCRIPT = """
$sessionManagerType = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType=WindowsRuntime]
if ($null -eq $sessionManagerType) {
    @{ available = $false } | ConvertTo-Json -Compress
    exit 0
}
$manager = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync().GetAwaiter().GetResult()
$session = $manager.GetCurrentSession()
if ($null -eq $session) {
    @{ available = $false } | ConvertTo-Json -Compress
    exit 0
}
$properties = $session.TryGetMediaPropertiesAsync().GetAwaiter().GetResult()
$timeline = $session.GetTimelineProperties()
$playbackInfo = $session.GetPlaybackInfo()
function Convert-HnsToSeconds($value) {
    if ($null -eq $value) {
        return $null
    }
    return [math]::Round(([double]$value.Duration / 10000000.0), 3)
}
@{
    available = $true
    title = $properties.Title
    artist = $properties.Artist
    source = $session.SourceAppUserModelId
    position = Convert-HnsToSeconds $timeline.Position
    duration = Convert-HnsToSeconds $timeline.EndTime
    playback = if ($null -eq $playbackInfo) { $null } else { [string]$playbackInfo.PlaybackStatus }
} | ConvertTo-Json -Compress
""".strip()


class WindowsMediaSessionReader:
    def __init__(
        self,
        runner: CommandRunner | None = None,
        audio_reader: AudioSessionReader | None = None,
        start_background_polling: bool = True,
    ) -> None:
        self._runner = runner or _run_command
        self._audio_reader = audio_reader or _read_from_audio_sessions
        self._powershell_retry_after = 0.0
        self._cached_snapshot = unavailable_media_session()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._poll_thread: threading.Thread | None = None
        if start_background_polling:
            self._cached_snapshot = self._poll_once()
            self._poll_thread = threading.Thread(target=self._poll_loop, name="media-session-reader", daemon=True)
            self._poll_thread.start()

    def read_current_session(self) -> MediaSessionSnapshot:
        if self._poll_thread is None:
            return self._poll_once()
        with self._lock:
            return self._cached_snapshot

    def close(self) -> None:
        self._stop_event.set()
        if self._poll_thread is not None:
            self._poll_thread.join(timeout=0.2)

    def _poll_loop(self) -> None:
        while not self._stop_event.wait(0.033):
            snapshot = self._poll_once()
            with self._lock:
                self._cached_snapshot = snapshot

    def _poll_once(self) -> MediaSessionSnapshot:
        audio_snapshot = self._audio_reader()
        now = time.monotonic()
        if now < self._powershell_retry_after:
            return audio_snapshot if audio_snapshot.is_available else unavailable_media_session()
        try:
            completed = self._runner(
                [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    POWERSHELL_MEDIA_SESSION_SCRIPT,
                ],
                2.5,
            )
        except (OSError, subprocess.TimeoutExpired):
            self._powershell_retry_after = now + 10.0
            return audio_snapshot if audio_snapshot.is_available else unavailable_media_session()

        if _is_blocked_powershell_result(completed.stderr):
            self._powershell_retry_after = now + 30.0
            return audio_snapshot if audio_snapshot.is_available else unavailable_media_session()

        payload = _extract_json_object(completed.stdout)
        if payload is None:
            return audio_snapshot if audio_snapshot.is_available else unavailable_media_session()

        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            return audio_snapshot if audio_snapshot.is_available else unavailable_media_session()

        if not decoded.get("available"):
            return audio_snapshot if audio_snapshot.is_available else unavailable_media_session()

        source_value = str(decoded.get("source") or "")
        return MediaSessionSnapshot(
            title=str(decoded.get("title") or "Unknown Track"),
            artist=str(decoded.get("artist") or "Unknown Artist"),
            source_app=format_source_app_name(source_value),
            position_seconds=_coerce_optional_seconds(decoded.get("position")),
            duration_seconds=_coerce_optional_seconds(decoded.get("duration")),
            audio_level=audio_snapshot.audio_level,
            is_playing=_coerce_playback_state(decoded.get("playback")) if decoded.get("playback") is not None else audio_snapshot.is_playing,
            is_available=True,
        )


def unavailable_media_session() -> MediaSessionSnapshot:
    return MediaSessionSnapshot(
        title="No active media",
        artist="Start playback in Spotify, YouTube, VLC, or another media app.",
        source_app="Waiting For Session",
        position_seconds=None,
        duration_seconds=None,
        audio_level=None,
        is_playing=None,
        is_available=False,
    )


def format_source_app_name(source_value: str) -> str:
    normalized = source_value.strip()
    if not normalized:
        return "Unknown Source"

    lowered = normalized.lower()
    known_patterns = (
        ("spotify", "Spotify"),
        ("chrome", "Chrome"),
        ("msedge", "Edge"),
        ("firefox", "Firefox"),
        ("vlc", "VLC"),
        ("itunes", "iTunes"),
        ("foobar", "Foobar2000"),
        ("music", "Media Player"),
    )
    for pattern, label in known_patterns:
        if pattern in lowered:
            return label

    primary = normalized.split("!")[-1]
    primary = primary.split(".")[-1]
    primary = primary.replace(".exe", "").replace("_", " ").replace("-", " ").strip()
    if not primary:
        return "Unknown Source"
    return " ".join(part.capitalize() for part in primary.split())


def _extract_json_object(stdout: str) -> str | None:
    start = stdout.find("{")
    end = stdout.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    return stdout[start : end + 1]


def _run_command(command: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _coerce_optional_seconds(value: object) -> float | None:
    try:
        if value is None:
            return None
        seconds = float(value)
    except (TypeError, ValueError):
        return None
    if seconds <= 0:
        return None
    return seconds


def _coerce_playback_state(value: object) -> bool | None:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return None
    if normalized == "playing":
        return True
    if normalized in {"paused", "stopped"}:
        return False
    return None


def _is_blocked_powershell_result(stderr: str) -> bool:
    lowered = stderr.lower()
    return (
        "constrainedlanguage" in lowered
        or "method invocation is supported only on core types" in lowered
        or "null-valued expression" in lowered
    )


def _read_from_audio_sessions() -> MediaSessionSnapshot:
    try:
        from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
    except ModuleNotFoundError:
        return unavailable_media_session()

    candidates: list[tuple[float, MediaSessionSnapshot]] = []
    for session in AudioUtilities.GetAllSessions():
        process = session.Process.name() if session.Process else ""
        display_name = str(session.DisplayName or "").strip()
        session_name = display_name or process
        if not session_name:
            continue
        lowered_process = process.lower()
        if lowered_process in {"audiodg.exe", "svchost.exe"}:
            continue

        try:
            meter = session._ctl.QueryInterface(IAudioMeterInformation)
            audio_level = round(float(meter.GetPeakValue()), 3)
        except Exception:
            audio_level = 0.0

        state = int(getattr(session, "State", 0))
        source_app = format_source_app_name(process or session_name)
        snapshot = MediaSessionSnapshot(
            title=source_app,
            artist="Active audio session",
            source_app=source_app,
            position_seconds=None,
            duration_seconds=None,
            audio_level=audio_level,
            is_playing=(audio_level > 0.01) or state == 1,
            is_available=True,
        )
        score = (120.0 if state == 1 else 0.0) + (audio_level * 100.0) + (15.0 if display_name else 0.0)
        candidates.append((score, snapshot))

    if not candidates:
        return unavailable_media_session()

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]
