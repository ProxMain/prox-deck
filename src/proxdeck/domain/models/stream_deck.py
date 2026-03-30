from __future__ import annotations

from dataclasses import dataclass


STREAM_DECK_LAUNCH_ACTION = "launch"
STREAM_DECK_GROUP_ACTION = "group"
STREAM_DECK_NOOP_ACTION = "noop"
STREAM_DECK_SUPPORTED_ACTION_TYPES = frozenset(
    {
        STREAM_DECK_LAUNCH_ACTION,
        STREAM_DECK_GROUP_ACTION,
        STREAM_DECK_NOOP_ACTION,
    }
)

STREAM_DECK_SIZE_VARIANT_COMPACT = "1/6"
STREAM_DECK_SIZE_VARIANT_TALL = "2/6-tall"
STREAM_DECK_SUPPORTED_SIZE_VARIANTS = frozenset(
    {
        STREAM_DECK_SIZE_VARIANT_COMPACT,
        STREAM_DECK_SIZE_VARIANT_TALL,
    }
)


@dataclass(frozen=True)
class StreamDeckButtonDefinition:
    button_id: str
    label: str
    icon: str | None
    action_type: str
    action_config: dict[str, object]


@dataclass(frozen=True)
class StreamDeckSettings:
    size_variant: str
    buttons: tuple[StreamDeckButtonDefinition, ...]
