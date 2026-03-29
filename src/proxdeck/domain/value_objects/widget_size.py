from __future__ import annotations

from dataclasses import dataclass


ALLOWED_WIDGET_AREAS = {1, 2, 4, 6}
SIZE_PRESET_DIMENSIONS: dict[str, tuple[int, int]] = {
    "1/6": (1, 1),
    "2/6-wide": (2, 1),
    "2/6-tall": (1, 2),
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
        try:
            width, height = SIZE_PRESET_DIMENSIONS[preset]
        except KeyError as error:
            raise ValueError(f"Unsupported widget size preset: {preset}") from error
        return cls(width * height), width, height
