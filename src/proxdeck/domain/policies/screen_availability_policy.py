from __future__ import annotations

from proxdeck.domain.exceptions.layout_errors import LockedScreenError
from proxdeck.domain.models.screen import Screen


class ScreenAvailabilityPolicy:
    def ensure_accessible(self, screen: Screen) -> None:
        if not screen.is_available():
            raise LockedScreenError(f"Screen '{screen.name}' is not available")
