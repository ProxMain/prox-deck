from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenSnapshot:
    name: str
    width: int
    height: int
    x: int
    y: int
