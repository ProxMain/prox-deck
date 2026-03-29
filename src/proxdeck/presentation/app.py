from __future__ import annotations

from proxdeck.application.controllers.management_controller import ManagementController
from proxdeck.application.controllers.runtime_controller import RuntimeController
from proxdeck.presentation.views.runtime_window import RuntimeWindow


class ProxDeckApplication:
    def __init__(
        self,
        runtime_controller: RuntimeController,
        management_controller: ManagementController,
    ) -> None:
        self._runtime_controller = runtime_controller
        self._management_controller = management_controller

    def build_window(self) -> RuntimeWindow:
        runtime_state = self._runtime_controller.load_runtime_state()
        return RuntimeWindow(
            management_controller=self._management_controller,
            runtime_controller=self._runtime_controller,
            runtime_state=runtime_state,
        )
