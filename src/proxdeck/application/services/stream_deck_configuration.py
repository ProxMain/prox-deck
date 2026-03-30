from __future__ import annotations

import copy

from proxdeck.domain.models.stream_deck import (
    STREAM_DECK_GROUP_ACTION,
    STREAM_DECK_LAUNCH_ACTION,
    STREAM_DECK_NOOP_ACTION,
    STREAM_DECK_SIZE_VARIANT_COMPACT,
    STREAM_DECK_SIZE_VARIANT_TALL,
    STREAM_DECK_SUPPORTED_ACTION_TYPES,
    STREAM_DECK_SUPPORTED_SIZE_VARIANTS,
    StreamDeckButtonDefinition,
    StreamDeckSettings,
)
from proxdeck.application.services.stream_deck_icon_normalization import (
    normalize_stream_deck_icon_value,
)

STREAM_DECK_DEFAULT_BUTTON_COUNT = 64


def build_default_stream_deck_settings(size_variant: str = STREAM_DECK_SIZE_VARIANT_COMPACT) -> dict[str, object]:
    normalized_variant = normalize_stream_deck_size_variant(size_variant)
    return {
        "size_variant": normalized_variant,
        "buttons": normalize_stream_deck_buttons(
            [
                {
                    "id": "browser",
                    "label": "Browser",
                    "icon": "asset:stream_deck_browser.svg",
                    "action_type": STREAM_DECK_LAUNCH_ACTION,
                    "action_config": {"target": "https://example.com"},
                },
                {
                    "id": "mail",
                    "label": "Mail",
                    "icon": "asset:stream_deck_mail.svg",
                    "action_type": STREAM_DECK_LAUNCH_ACTION,
                    "action_config": {"target": "mailto:"},
                },
                {
                    "id": "work",
                    "label": "Work",
                    "icon": "asset:stream_deck_folder.svg",
                    "action_type": STREAM_DECK_GROUP_ACTION,
                    "action_config": {
                        "children": [
                            {
                                "id": "chat",
                                "label": "Chat",
                                "icon": "asset:stream_deck_chat.svg",
                                "action_type": STREAM_DECK_NOOP_ACTION,
                                "action_config": {},
                            },
                            {
                                "id": "calendar",
                                "label": "Calendar",
                                "icon": "asset:stream_deck_calendar.svg",
                                "action_type": STREAM_DECK_NOOP_ACTION,
                                "action_config": {},
                            },
                        ]
                    },
                },
                {
                    "id": "settings",
                    "label": "Settings",
                    "icon": "asset:stream_deck_settings.svg",
                    "action_type": STREAM_DECK_LAUNCH_ACTION,
                    "action_config": {"target": "ms-settings:"},
                },
            ]
        ),
    }


def parse_stream_deck_settings(settings: dict[str, object]) -> StreamDeckSettings:
    size_variant = normalize_stream_deck_size_variant(settings.get("size_variant"))
    raw_buttons = settings.get("buttons")
    if not isinstance(raw_buttons, list):
        raw_buttons = build_default_stream_deck_settings(size_variant)["buttons"]
    buttons = tuple(_parse_button_definition(button) for button in normalize_stream_deck_buttons(raw_buttons))
    if not buttons:
        return parse_stream_deck_settings(build_default_stream_deck_settings(size_variant))
    return StreamDeckSettings(size_variant=size_variant, buttons=buttons)


def build_stream_deck_settings_payload(
    size_variant: str,
    buttons: list[dict[str, object]],
) -> dict[str, object]:
    normalized_buttons = normalize_stream_deck_buttons(buttons)
    if not normalized_buttons:
        raise ValueError("Stream Deck widgets require at least one button definition")
    return {
        "size_variant": normalize_stream_deck_size_variant(size_variant),
        "buttons": normalized_buttons,
    }


def normalize_stream_deck_action_type(action_type: object) -> str:
    normalized = str(action_type or STREAM_DECK_NOOP_ACTION).strip().lower()
    if normalized in STREAM_DECK_SUPPORTED_ACTION_TYPES:
        return normalized
    return STREAM_DECK_NOOP_ACTION


def normalize_stream_deck_size_variant(size_variant: object) -> str:
    normalized = str(size_variant or STREAM_DECK_SIZE_VARIANT_COMPACT).strip().lower()
    alias_map = {
        "1": STREAM_DECK_SIZE_VARIANT_COMPACT,
        "1/6": STREAM_DECK_SIZE_VARIANT_COMPACT,
        "compact": STREAM_DECK_SIZE_VARIANT_COMPACT,
        "2": STREAM_DECK_SIZE_VARIANT_TALL,
        "2/6": STREAM_DECK_SIZE_VARIANT_TALL,
        "2/6-tall": STREAM_DECK_SIZE_VARIANT_TALL,
        "2/6-vertical": STREAM_DECK_SIZE_VARIANT_TALL,
        "tall": STREAM_DECK_SIZE_VARIANT_TALL,
    }
    candidate = alias_map.get(normalized, normalized)
    if candidate in STREAM_DECK_SUPPORTED_SIZE_VARIANTS:
        return candidate
    return STREAM_DECK_SIZE_VARIANT_COMPACT


def normalize_stream_deck_arguments(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def normalize_stream_deck_buttons(
    raw_buttons: list[object],
    *,
    fill_to_count: bool = True,
) -> list[dict[str, object]]:
    normalized_buttons: list[dict[str, object]] = []
    for index, raw_button in enumerate(raw_buttons[:STREAM_DECK_DEFAULT_BUTTON_COUNT]):
        if not isinstance(raw_button, dict):
            continue
        normalized_buttons.append(_normalize_stream_deck_button(raw_button, index))
    if fill_to_count:
        while len(normalized_buttons) < STREAM_DECK_DEFAULT_BUTTON_COUNT:
            normalized_buttons.append(build_empty_stream_deck_button(len(normalized_buttons)))
    return normalized_buttons


def build_empty_stream_deck_button(index: int) -> dict[str, object]:
    return {
        "id": f"button-{index + 1}",
        "label": f"Button {index + 1}",
        "icon": "",
        "action_type": STREAM_DECK_NOOP_ACTION,
        "action_config": {},
    }


def deep_copy_stream_deck_buttons(buttons: list[dict[str, object]]) -> list[dict[str, object]]:
    return copy.deepcopy(buttons)


def collect_stream_deck_page_options(buttons: list[dict[str, object]]) -> list[tuple[str, str]]:
    options: list[tuple[str, str]] = [("", "Root")]
    for button in buttons:
        _append_page_options(options, button=button, parent_path="")
    return options


def get_stream_deck_buttons_for_path(
    buttons: list[dict[str, object]],
    path: str,
) -> list[dict[str, object]]:
    if not path:
        return buttons
    current_buttons = buttons
    for segment in path.split("/"):
        match = next((button for button in current_buttons if button.get("id") == segment), None)
        if match is None:
            return []
        action_config = match.get("action_config")
        if not isinstance(action_config, dict):
            return []
        children = action_config.get("children")
        if not isinstance(children, list):
            return []
        current_buttons = children
    return current_buttons


def child_button_definitions(button: StreamDeckButtonDefinition) -> tuple[StreamDeckButtonDefinition, ...]:
    raw_children = button.action_config.get("children")
    if not isinstance(raw_children, list):
        return ()
    return tuple(
        _parse_button_definition(child)
        for child in normalize_stream_deck_buttons(raw_children)
    )


def visible_stream_deck_button_count(size_variant: str) -> int:
    normalized_variant = normalize_stream_deck_size_variant(size_variant)
    if normalized_variant == STREAM_DECK_SIZE_VARIANT_TALL:
        return 32
    return 16


def stream_deck_dimensions_for_variant(size_variant: str) -> tuple[int, int]:
    normalized_variant = normalize_stream_deck_size_variant(size_variant)
    if normalized_variant == STREAM_DECK_SIZE_VARIANT_TALL:
        return (1, 2)
    return (1, 1)


def stream_deck_variant_for_dimensions(width: int, height: int) -> str:
    if (width, height) == (1, 2):
        return STREAM_DECK_SIZE_VARIANT_TALL
    if (width, height) == (1, 1):
        return STREAM_DECK_SIZE_VARIANT_COMPACT
    raise ValueError("Stream Deck widgets only support 1/6 and 2/6-tall placements")


def _normalize_stream_deck_button(raw_button: dict[str, object], index: int) -> dict[str, object]:
    label = str(raw_button.get("label", "")).strip() or f"Button {index + 1}"
    icon = normalize_stream_deck_icon_value(str(raw_button.get("icon", "")).strip())
    action_type = normalize_stream_deck_action_type(raw_button.get("action_type"))
    raw_action_config = raw_button.get("action_config")
    action_config = raw_action_config if isinstance(raw_action_config, dict) else {}
    normalized_action_config: dict[str, object] = {}
    if action_type == STREAM_DECK_LAUNCH_ACTION:
        normalized_action_config = {
            "target": str(action_config.get("target", "")).strip(),
            "arguments": normalize_stream_deck_arguments(action_config.get("arguments")),
        }
    elif action_type == STREAM_DECK_GROUP_ACTION:
        raw_children = action_config.get("children")
        children = raw_children if isinstance(raw_children, list) else []
        normalized_action_config = {
            "children": normalize_stream_deck_buttons(children, fill_to_count=False)
        }
    return {
        "id": str(raw_button.get("id", f"button-{index + 1}")).strip() or f"button-{index + 1}",
        "label": label,
        "icon": icon,
        "action_type": action_type,
        "action_config": normalized_action_config,
    }


def _parse_button_definition(raw_button: dict[str, object]) -> StreamDeckButtonDefinition:
    return StreamDeckButtonDefinition(
        button_id=str(raw_button.get("id", "")).strip(),
        label=str(raw_button.get("label", "")).strip(),
        icon=normalize_stream_deck_icon_value(str(raw_button.get("icon", "")).strip()) or None,
        action_type=str(raw_button.get("action_type", STREAM_DECK_NOOP_ACTION)).strip(),
        action_config=copy.deepcopy(raw_button.get("action_config", {})),
    )


def _append_page_options(
    options: list[tuple[str, str]],
    button: dict[str, object],
    parent_path: str,
) -> None:
    if button.get("action_type") != STREAM_DECK_GROUP_ACTION:
        return
    button_id = str(button.get("id", "")).strip()
    if not button_id:
        return
    path = button_id if not parent_path else f"{parent_path}/{button_id}"
    label = str(button.get("label", "Folder")).strip() or "Folder"
    options.append((path, label))
    action_config = button.get("action_config")
    if not isinstance(action_config, dict):
        return
    children = action_config.get("children")
    if not isinstance(children, list):
        return
    for child in children:
        if isinstance(child, dict):
            _append_page_options(options, button=child, parent_path=path)
