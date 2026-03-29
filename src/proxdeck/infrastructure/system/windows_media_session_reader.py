from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MediaSessionSnapshot:
    title: str
    artist: str
    source_app: str
    position_seconds: float | None
    duration_seconds: float | None
    is_playing: bool | None
    is_available: bool


class CommandRunner(Protocol):
    def __call__(self, command: list[str], timeout: float) -> subprocess.CompletedProcess[str]: ...


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
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self._runner = runner or _run_command

    def read_current_session(self) -> MediaSessionSnapshot:
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
            return unavailable_media_session()

        payload = _extract_json_object(completed.stdout)
        if payload is None:
            return unavailable_media_session()

        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            return unavailable_media_session()

        if not decoded.get("available"):
            return unavailable_media_session()

        source_value = str(decoded.get("source") or "")
        return MediaSessionSnapshot(
            title=str(decoded.get("title") or "Unknown Track"),
            artist=str(decoded.get("artist") or "Unknown Artist"),
            source_app=format_source_app_name(source_value),
            position_seconds=_coerce_optional_seconds(decoded.get("position")),
            duration_seconds=_coerce_optional_seconds(decoded.get("duration")),
            is_playing=_coerce_playback_state(decoded.get("playback")),
            is_available=True,
        )


def unavailable_media_session() -> MediaSessionSnapshot:
    return MediaSessionSnapshot(
        title="No active media",
        artist="Start playback in Spotify, YouTube, VLC, or another media app.",
        source_app="Waiting For Session",
        position_seconds=None,
        duration_seconds=None,
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
