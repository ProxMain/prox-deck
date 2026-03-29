from __future__ import annotations

from proxdeck.application.dto.runtime_state import RuntimeState
from proxdeck.application.services.runtime_startup_service import RuntimeStartupService
from proxdeck.application.services.screen_service import ScreenService


class RuntimeController:
    def __init__(
        self,
        runtime_startup_service: RuntimeStartupService,
        screen_service: ScreenService,
    ) -> None:
        self._runtime_startup_service = runtime_startup_service
        self._screen_service = screen_service

    def load_runtime_state(self) -> RuntimeState:
        return self._runtime_startup_service.build_runtime_state()

    def switch_screen(self, screen_id: str):
        return self._screen_service.switch_screen(screen_id)
