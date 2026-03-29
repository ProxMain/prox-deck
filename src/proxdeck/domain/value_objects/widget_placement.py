from __future__ import annotations

from dataclasses import dataclass

from proxdeck.domain.value_objects.widget_size import WidgetSize


@dataclass(frozen=True)
class WidgetPlacement:
    column: int
    row: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.column < 0 or self.row < 0:
            raise ValueError("Placement origin must be positive")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Placement dimensions must be positive")
        WidgetSize(self.area)

    @property
    def area(self) -> int:
        return self.width * self.height

    def cells(self) -> set[tuple[int, int]]:
        return {
            (self.column + column_offset, self.row + row_offset)
            for column_offset in range(self.width)
            for row_offset in range(self.height)
        }
