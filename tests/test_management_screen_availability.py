import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.screen_availability import ScreenAvailability
from proxdeck.domain.models.screen_layout import ScreenLayout
from proxdeck.presentation.views.management_view import ManagementView


class StubManagementController:
    def __init__(self, screens) -> None:
        from proxdeck.application.dto.management_state import ManagementState

        self._state = ManagementState(screens=tuple(screens), widget_definitions=tuple())

    def load_management_state(self):
        return self._state


def test_management_status_text_for_available_screen() -> None:
    screen = Screen(
        screen_id="gaming",
        name="Gaming",
        availability=ScreenAvailability.AVAILABLE,
        layout=ScreenLayout(),
    )

    status = ManagementView.build_screen_ui_state(screen).status_text

    assert status == "Gaming is editable."


def test_management_status_text_for_soon_screen() -> None:
    screen = Screen(
        screen_id="developing",
        name="Developing",
        availability=ScreenAvailability.SOON,
        layout=ScreenLayout(),
    )

    status = ManagementView.build_screen_ui_state(screen).status_text

    assert status == "Developing is not editable yet. This screen is marked Soon."


def test_management_view_disables_controls_for_soon_screen() -> None:
    app = QApplication.instance() or QApplication([])
    screen = Screen(
        screen_id="developing",
        name="Developing",
        availability=ScreenAvailability.SOON,
        layout=ScreenLayout(),
    )
    view = ManagementView(StubManagementController([screen]))

    assert view._management_status_label.text() == "Developing is not editable yet. This screen is marked Soon."
    assert view._save_web_button.isEnabled() is False
    assert view._management_widget_selector.isEnabled() is False
    assert view._widget_palette.isEnabled() is False
    assert view._layout_preview.isEnabled() is False

    view.deleteLater()
    app.processEvents()


def test_management_view_enables_controls_for_available_screen() -> None:
    app = QApplication.instance() or QApplication([])
    screen = Screen(
        screen_id="gaming",
        name="Gaming",
        availability=ScreenAvailability.AVAILABLE,
        layout=ScreenLayout(),
    )
    view = ManagementView(StubManagementController([screen]))

    assert view._management_status_label.text() == "Gaming is editable."
    assert view._save_web_button.isEnabled() is True
    assert view._management_widget_selector.isEnabled() is True
    assert view._widget_palette.isEnabled() is True
    assert view._layout_preview.isEnabled() is True

    view.deleteLater()
    app.processEvents()
