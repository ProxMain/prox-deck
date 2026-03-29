from __future__ import annotations

from enum import Enum


class WidgetKind(str, Enum):
    BUILTIN = "builtin"
    INSTALLABLE = "installable"
