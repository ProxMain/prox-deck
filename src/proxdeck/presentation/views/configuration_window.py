from __future__ import annotations

from collections.abc import Callable

from proxdeck.application.controllers.management_controller import ManagementController
from proxdeck.bootstrap.settings import APP_RELEASE
from proxdeck.presentation.views.management_view import ManagementView

try:
    from PySide6.QtWidgets import QMainWindow
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QMainWindow = object


class ConfigurationWindow(QMainWindow):
    def __init__(
        self,
        management_controller: ManagementController,
        on_state_changed: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle(f"Prox Deck {APP_RELEASE} // Control Room")
        self.resize(1440, 920)
        self._management_view = ManagementView(
            management_controller=management_controller,
            on_state_changed=on_state_changed,
        )
        self.setCentralWidget(self._management_view)

    @property
    def management_view(self) -> ManagementView:
        return self._management_view
