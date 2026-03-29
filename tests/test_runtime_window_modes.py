import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from proxdeck.application.dto.management_state import ManagementState
from proxdeck.application.dto.runtime_state import RuntimeState
from proxdeck.domain.models.runtime_target import RuntimeTarget
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.screen_availability import ScreenAvailability
from proxdeck.domain.models.screen_layout import ScreenLayout
from proxdeck.presentation.views.runtime_window import RuntimeWindow


class StubManagementController:
    def __init__(self, screens) -> None:
        self._state = ManagementState(screens=tuple(screens), widget_definitions=tuple())

    def load_management_state(self):
        return self._state


class StubRuntimeController:
    def __init__(self, screens) -> None:
        self._screens = {screen.screen_id: screen for screen in screens}

    def switch_screen(self, screen_id: str):
        screen = self._screens.get(screen_id)
        if screen is None:
            raise ValueError(f"Unknown screen: {screen_id}")
        return screen


def test_runtime_window_uses_dashboard_only_layout_for_detected_target() -> None:
    app = QApplication.instance() or QApplication([])
    screen = _build_screen()
    window = RuntimeWindow(
        management_controller=StubManagementController([screen]),
        runtime_controller=StubRuntimeController([screen]),
        runtime_state=RuntimeState(
            active_screen=screen,
            available_screens=(screen,),
            runtime_target=RuntimeTarget(
                monitor_name="CORSAIR Xeneon Edge",
                width=1600,
                height=480,
                x=1920,
                y=0,
            ),
        ),
    )

    layout = window.centralWidget().layout()

    assert window._screen_selector is None
    assert layout.contentsMargins().left() == 0
    assert layout.contentsMargins().top() == 0

    window.deleteLater()
    app.processEvents()


def test_runtime_window_keeps_management_shell_in_fallback_mode() -> None:
    app = QApplication.instance() or QApplication([])
    screen = _build_screen()
    window = RuntimeWindow(
        management_controller=StubManagementController([screen]),
        runtime_controller=StubRuntimeController([screen]),
        runtime_state=RuntimeState(
            active_screen=screen,
            available_screens=(screen,),
            runtime_target=None,
        ),
    )

    layout = window.centralWidget().layout()

    assert window._screen_selector is not None
    assert layout.contentsMargins().left() == 24
    assert layout.contentsMargins().top() == 24

    window.deleteLater()
    app.processEvents()


def test_runtime_window_locks_dashboard_grid_to_even_three_by_two_cell_distribution() -> None:
    app = QApplication.instance() or QApplication([])
    screen = _build_screen()
    window = RuntimeWindow(
        management_controller=StubManagementController([screen]),
        runtime_controller=StubRuntimeController([screen]),
        runtime_state=RuntimeState(
            active_screen=screen,
            available_screens=(screen,),
            runtime_target=None,
        ),
    )

    grid = window._dashboard_grid

    assert grid is not None
    assert [grid.columnStretch(index) for index in range(3)] == [1, 1, 1]
    assert [grid.rowStretch(index) for index in range(2)] == [1, 1]

    window.deleteLater()
    app.processEvents()


def test_runtime_window_switches_to_next_screen_relative_to_active_screen() -> None:
    app = QApplication.instance() or QApplication([])
    gaming = _build_screen(screen_id="gaming", name="Gaming")
    performance = _build_screen(screen_id="performance", name="Performance")
    window = RuntimeWindow(
        management_controller=StubManagementController([gaming, performance]),
        runtime_controller=StubRuntimeController([gaming, performance]),
        runtime_state=RuntimeState(
            active_screen=gaming,
            available_screens=(gaming, performance),
            runtime_target=None,
        ),
    )

    window._switch_relative_screen(1)

    assert window._runtime_state.active_screen.screen_id == "performance"

    window.deleteLater()
    app.processEvents()


def test_runtime_window_wraps_to_previous_screen_when_swiping_back() -> None:
    app = QApplication.instance() or QApplication([])
    gaming = _build_screen(screen_id="gaming", name="Gaming")
    performance = _build_screen(screen_id="performance", name="Performance")
    window = RuntimeWindow(
        management_controller=StubManagementController([gaming, performance]),
        runtime_controller=StubRuntimeController([gaming, performance]),
        runtime_state=RuntimeState(
            active_screen=gaming,
            available_screens=(gaming, performance),
            runtime_target=None,
        ),
    )

    window._switch_relative_screen(-1)

    assert window._runtime_state.active_screen.screen_id == "performance"

    window.deleteLater()
    app.processEvents()


def _build_screen(screen_id: str = "gaming", name: str = "Gaming") -> Screen:
    return Screen(
        screen_id=screen_id,
        name=name,
        availability=ScreenAvailability.AVAILABLE,
        layout=ScreenLayout(),
    )
