from __future__ import annotations

from dataclasses import dataclass


ALLOWED_WIDGET_AREAS = {1, 2, 4, 6}
SIZE_PRESET_DIMENSIONS: dict[str, tuple[int, int]] = {
    "1/6": (1, 1),
    "2/6-wide": (2, 1),
    "2/6-tall": (1, 2),
    "2/6-horizontal": (2, 1),
    "2/6-vertical": (1, 2),
    "4/6": (2, 2),
    "6/6": (3, 2),
}


@dataclass(frozen=True)
class WidgetSize:
    area: int

    def __post_init__(self) -> None:
        if self.area not in ALLOWED_WIDGET_AREAS:
            raise ValueError(f"Unsupported widget size: {self.area}")

    @classmethod
    def from_preset(cls, preset: str) -> tuple["WidgetSize", int, int]:
        preset = normalize_size_preset(preset)
        try:
            width, height = SIZE_PRESET_DIMENSIONS[preset]
        except KeyError as error:
            raise ValueError(f"Unsupported widget size preset: {preset}") from error
        return cls(width * height), width, height


def normalize_size_preset(preset: str) -> str:
    normalized = str(preset).strip().lower()
    alias_map = {
        "1": "1/6",
        "1/6": "1/6",
        "2w": "2/6-wide",
        "2-wide": "2/6-wide",
        "2/6-wide": "2/6-wide",
        "2/6-horizontal": "2/6-wide",
        "2t": "2/6-tall",
        "2h": "2/6-tall",
        "2-tall": "2/6-tall",
        "2/6-tall": "2/6-tall",
        "2/6-vertical": "2/6-tall",
        "4": "4/6",
        "4/6": "4/6",
        "6": "6/6",
        "6/6": "6/6",
    }
    return alias_map.get(normalized, normalized)
