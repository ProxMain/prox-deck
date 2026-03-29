from __future__ import annotations

from enum import Enum


class ScreenAvailability(str, Enum):
    AVAILABLE = "available"
    LOCKED = "locked"
    SOON = "soon"
