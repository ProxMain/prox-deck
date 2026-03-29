from __future__ import annotations

from dataclasses import dataclass, field

from proxdeck.domain.models.screen_availability import ScreenAvailability
from proxdeck.domain.models.screen_layout import ScreenLayout


@dataclass(frozen=True)
class Screen:
    screen_id: str
    name: str
    availability: ScreenAvailability
    layout: ScreenLayout
    state: dict[str, object] = field(default_factory=dict)

    def is_available(self) -> bool:
        return self.availability is ScreenAvailability.AVAILABLE
