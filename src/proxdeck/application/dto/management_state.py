from __future__ import annotations

from dataclasses import dataclass

from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.widget_definition import WidgetDefinition


@dataclass(frozen=True)
class ManagementState:
    screens: tuple[Screen, ...]
    widget_definitions: tuple[WidgetDefinition, ...]
