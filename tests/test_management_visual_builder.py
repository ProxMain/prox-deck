import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from proxdeck.application.dto.management_state import ManagementState
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.screen_availability import ScreenAvailability
from proxdeck.domain.models.screen_layout import ScreenLayout
from proxdeck.domain.models.widget_compatibility import WidgetCompatibility
from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_install_metadata import WidgetInstallMetadata
from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.domain.value_objects.app_version import AppVersion
from proxdeck.domain.value_objects.capability_set import CapabilitySet
from proxdeck.domain.value_objects.widget_placement import WidgetPlacement
from proxdeck.presentation.views.management_view import ManagementView


class StubManagementController:
    def __init__(self, state: ManagementState) -> None:
        self._state = state
        self.add_calls: list[tuple[str, str, int, int, str]] = []
        self.move_calls: list[tuple[str, str, int, int]] = []

    def load_management_state(self):
        return self._state

    def add_widget_instance_smart(
        self,
        screen_id: str,
        widget_id: str,
        preferred_column: int,
        preferred_row: int,
        size_preset: str,
    ):
        self.add_calls.append(
            (screen_id, widget_id, preferred_column, preferred_row, size_preset)
        )
        return self._state.screens[0]

    def move_widget_instance_smart(
        self,
        screen_id: str,
        instance_id: str,
        preferred_column: int,
        preferred_row: int,
    ):
        self.move_calls.append((screen_id, instance_id, preferred_column, preferred_row))
        return self._state.screens[0]


def test_palette_selection_arms_click_to_place_mode() -> None:
    app = QApplication.instance() or QApplication([])
    controller = StubManagementController(_build_state())
    view = ManagementView(controller)

    view._handle_palette_select("clock")

    assert view._selected_palette_widget_id == "clock"
    assert "Click a slot to place it." in view._management_status_label.text()

    view.deleteLater()
    app.processEvents()


def test_clicking_cell_after_palette_selection_adds_widget() -> None:
    app = QApplication.instance() or QApplication([])
    controller = StubManagementController(_build_state())
    view = ManagementView(controller)

    view._handle_palette_select("clock")
    view._handle_preview_cell_activate(2, 1)

    assert controller.add_calls == [("gaming", "clock", 2, 1, "1/6")]

    view.deleteLater()
    app.processEvents()


def test_clicking_cell_after_selecting_tile_moves_widget() -> None:
    app = QApplication.instance() or QApplication([])
    controller = StubManagementController(_build_state())
    view = ManagementView(controller)

    view._handle_preview_select("clock-1")
    view._handle_preview_cell_activate(2, 1)

    assert controller.move_calls == [("gaming", "clock-1", 2, 1)]

    view.deleteLater()
    app.processEvents()


def _build_state() -> ManagementState:
    return ManagementState(
        screens=(
            Screen(
                screen_id="gaming",
                name="Gaming",
                availability=ScreenAvailability.AVAILABLE,
                layout=ScreenLayout(
                    widget_instances=(
                        WidgetInstance(
                            instance_id="clock-1",
                            widget_id="clock",
                            screen_id="gaming",
                            placement=WidgetPlacement(column=0, row=0, width=1, height=1),
                        ),
                    )
                ),
            ),
        ),
        widget_definitions=(
            WidgetDefinition(
                widget_id="clock",
                display_name="Clock",
                version="1.0.0",
                kind=WidgetKind.BUILTIN,
                compatibility=WidgetCompatibility(
                    minimum_app_version=AppVersion.parse("1.0.0")
                ),
                install_metadata=WidgetInstallMetadata(
                    distribution="core",
                    installation_scope="bundled",
                ),
                capabilities=CapabilitySet(frozenset()),
                entrypoint="widgets.clock",
            ),
        ),
    )
