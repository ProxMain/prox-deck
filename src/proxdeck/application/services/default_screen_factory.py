from __future__ import annotations

from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.screen_availability import ScreenAvailability
from proxdeck.domain.models.screen_layout import ScreenLayout


class DefaultScreenFactory:
    def create_defaults(self) -> list[Screen]:
        return [
            Screen(
                screen_id="gaming",
                name="Gaming",
                availability=ScreenAvailability.AVAILABLE,
                layout=ScreenLayout(),
            ),
            Screen(
                screen_id="performance",
                name="Performance",
                availability=ScreenAvailability.AVAILABLE,
                layout=ScreenLayout(),
            ),
            Screen(
                screen_id="streaming",
                name="Streaming",
                availability=ScreenAvailability.AVAILABLE,
                layout=ScreenLayout(),
            ),
            Screen(
                screen_id="developing",
                name="Developing",
                availability=ScreenAvailability.SOON,
                layout=ScreenLayout(),
            ),
        ]
