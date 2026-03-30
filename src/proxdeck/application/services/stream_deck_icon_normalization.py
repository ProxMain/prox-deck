from __future__ import annotations


STREAM_DECK_LEGACY_ICON_MAP: dict[str, str] = {
    "WWW": "asset:stream_deck_browser.svg",
    "OUT": "asset:stream_deck_mail.svg",
    "DIR": "asset:stream_deck_folder.svg",
    "SYS": "asset:stream_deck_settings.svg",
    "MSG": "asset:stream_deck_chat.svg",
    "CAL": "asset:stream_deck_calendar.svg",
    "CMD": "asset:stream_deck_terminal.svg",
    "AUD": "asset:stream_deck_play.svg",
    "ZEN": "asset:stream_deck_note.svg",
    "DSC": "asset:stream_deck_chat.svg",
    "YT": "asset:stream_deck_youtube.svg",
    "STEAM": "asset:stream_deck_steam.svg",
}


def normalize_stream_deck_icon_value(icon_value: str) -> str:
    normalized = str(icon_value).strip()
    if not normalized:
        return ""
    if normalized.lower().startswith("asset:"):
        return normalized
    return STREAM_DECK_LEGACY_ICON_MAP.get(normalized.upper(), normalized)
