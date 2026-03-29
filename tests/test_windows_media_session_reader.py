import subprocess

from proxdeck.infrastructure.system.windows_media_session_reader import (
    MediaSessionSnapshot,
    WindowsMediaSessionReader,
    format_source_app_name,
    unavailable_media_session,
)


def test_format_source_app_name_maps_common_sources() -> None:
    assert format_source_app_name("SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify") == "Spotify"
    assert format_source_app_name("msedge.exe") == "Edge"
    assert format_source_app_name("chrome.exe") == "Chrome"


def test_reader_returns_unavailable_when_no_session_is_reported() -> None:
    def runner(command: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout='{"available":false}', stderr="")

    reader = WindowsMediaSessionReader(
        runner=runner,
        audio_reader=unavailable_media_session,
        start_background_polling=False,
    )

    assert reader.read_current_session() == unavailable_media_session()


def test_reader_builds_snapshot_from_media_payload() -> None:
    def runner(command: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='{"available":true,"title":"Nightcall","artist":"Kavinsky","source":"SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify"}',
            stderr="",
        )

    reader = WindowsMediaSessionReader(
        runner=runner,
        audio_reader=unavailable_media_session,
        start_background_polling=False,
    )

    assert reader.read_current_session() == MediaSessionSnapshot(
        title="Nightcall",
        artist="Kavinsky",
        source_app="Spotify",
        position_seconds=None,
        duration_seconds=None,
        audio_level=None,
        is_playing=None,
        is_available=True,
    )


def test_reader_builds_snapshot_with_timeline_payload() -> None:
    def runner(command: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                '{"available":true,"title":"Nightcall","artist":"Kavinsky",'
                '"source":"SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify",'
                '"position":42.5,"duration":180.0,"playback":"Playing"}'
            ),
            stderr="",
        )

    reader = WindowsMediaSessionReader(
        runner=runner,
        audio_reader=unavailable_media_session,
        start_background_polling=False,
    )

    assert reader.read_current_session() == MediaSessionSnapshot(
        title="Nightcall",
        artist="Kavinsky",
        source_app="Spotify",
        position_seconds=42.5,
        duration_seconds=180.0,
        audio_level=None,
        is_playing=True,
        is_available=True,
    )
