from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GridSize:
    columns: int
    rows: int

    @property
    def capacity(self) -> int:
        return self.columns * self.rows

    def contains(self, column: int, row: int) -> bool:
        return 0 <= column < self.columns and 0 <= row < self.rows
