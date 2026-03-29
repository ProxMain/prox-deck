from __future__ import annotations

from dataclasses import dataclass


ALLOWED_WIDGET_AREAS = {1, 2, 4, 6}


@dataclass(frozen=True)
class WidgetSize:
    area: int

    def __post_init__(self) -> None:
        if self.area not in ALLOWED_WIDGET_AREAS:
            raise ValueError(f"Unsupported widget size: {self.area}")
