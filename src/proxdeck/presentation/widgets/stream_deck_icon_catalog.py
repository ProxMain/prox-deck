from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from proxdeck.application.services.stream_deck_icon_normalization import (
    normalize_stream_deck_icon_value,
)


@dataclass(frozen=True)
class StreamDeckIconOption:
    value: str
    label: str
    asset_name: str


STREAM_DECK_ICON_OPTIONS: tuple[StreamDeckIconOption, ...] = (
    StreamDeckIconOption("asset:stream_deck_youtube.svg", "YouTube", "stream_deck_youtube.svg"),
    StreamDeckIconOption("asset:stream_deck_discord.svg", "Discord", "stream_deck_discord.svg"),
    StreamDeckIconOption("asset:stream_deck_browser.svg", "Browser", "stream_deck_browser.svg"),
    StreamDeckIconOption("asset:stream_deck_mail.svg", "Mail", "stream_deck_mail.svg"),
    StreamDeckIconOption("asset:stream_deck_folder.svg", "Folder", "stream_deck_folder.svg"),
    StreamDeckIconOption("asset:stream_deck_settings.svg", "Settings", "stream_deck_settings.svg"),
    StreamDeckIconOption("asset:stream_deck_chat.svg", "Chat", "stream_deck_chat.svg"),
    StreamDeckIconOption("asset:stream_deck_calendar.svg", "Calendar", "stream_deck_calendar.svg"),
    StreamDeckIconOption("asset:stream_deck_terminal.svg", "Terminal", "stream_deck_terminal.svg"),
    StreamDeckIconOption("asset:stream_deck_note.svg", "Notes", "stream_deck_note.svg"),
    StreamDeckIconOption("asset:stream_deck_play.svg", "Media", "stream_deck_play.svg"),
    StreamDeckIconOption("asset:stream_deck_link.svg", "Link", "stream_deck_link.svg"),
    StreamDeckIconOption("asset:stream_deck_steam.svg", "Steam", "stream_deck_steam.svg"),
)

def icon_catalog_asset_path(asset_name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / asset_name


def resolve_stream_deck_icon_asset(icon_value: str) -> Path | None:
    normalized = normalize_stream_deck_icon_value(icon_value)
    if not normalized.lower().startswith("asset:"):
        candidate = Path(normalized)
        if candidate.exists():
            return candidate
        return None
    asset_name = normalized.split(":", 1)[1].strip()
    if not asset_name:
        return None
    asset_path = icon_catalog_asset_path(asset_name)
    if not asset_path.exists():
        return None
    return asset_path
