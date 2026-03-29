from __future__ import annotations

from dataclasses import dataclass

from proxdeck.domain.models.runtime_target import RuntimeTarget
from proxdeck.domain.models.screen import Screen


@dataclass(frozen=True)
class RuntimeState:
    active_screen: Screen
    available_screens: tuple[Screen, ...]
    runtime_target: RuntimeTarget | None
