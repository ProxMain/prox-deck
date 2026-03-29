import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from proxdeck.application.dto.management_state import ManagementState
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.screen_availability import ScreenAvailability
from proxdeck.domain.models.screen_layout import ScreenLayout
from proxdeck.presentation.views.configuration_window import ConfigurationWindow


class StubManagementController:
    def __init__(self, screens) -> None:
        self._state = ManagementState(screens=tuple(screens), widget_definitions=tuple())

    def load_management_state(self):
        return self._state


def test_configuration_window_wraps_management_view() -> None:
    app = QApplication.instance() or QApplication([])
    screen = Screen(
        screen_id="gaming",
        name="Gaming",
        availability=ScreenAvailability.AVAILABLE,
        layout=ScreenLayout(),
    )
    window = ConfigurationWindow(StubManagementController([screen]))

    assert window.windowTitle() == "Prox Deck // Control Room"
    assert window.centralWidget() is window.management_view

    window.deleteLater()
    app.processEvents()
