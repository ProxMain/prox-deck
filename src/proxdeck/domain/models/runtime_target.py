from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeTarget:
    monitor_name: str
    width: int
    height: int
    x: int
    y: int
