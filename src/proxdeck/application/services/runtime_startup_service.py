from __future__ import annotations

from proxdeck.application.dto.runtime_state import RuntimeState
from proxdeck.application.services.screen_service import ScreenService
from proxdeck.domain.contracts.runtime_target_detector import RuntimeTargetDetector


class RuntimeStartupService:
    def __init__(
        self,
        screen_service: ScreenService,
        runtime_target_detector: RuntimeTargetDetector,
    ) -> None:
        self._screen_service = screen_service
        self._runtime_target_detector = runtime_target_detector

    def build_runtime_state(self) -> RuntimeState:
        screens = self._screen_service.list_screens()
        return RuntimeState(
            active_screen=self._screen_service.get_active_screen(),
            available_screens=tuple(screens),
            runtime_target=self._runtime_target_detector.detect_target(),
        )
