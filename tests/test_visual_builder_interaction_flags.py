import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel

from proxdeck.application.dto.management_state import ManagementState
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.screen_availability import ScreenAvailability
from proxdeck.domain.models.screen_layout import ScreenLayout
from proxdeck.domain.models.widget_compatibility import WidgetCompatibility
from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_install_metadata import WidgetInstallMetadata
from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.domain.value_objects.app_version import AppVersion
from proxdeck.domain.value_objects.capability_set import CapabilitySet
from proxdeck.presentation.views.management_view import ManagementView


class StubManagementController:
    def __init__(self, state: ManagementState) -> None:
        self._state = state

    def load_management_state(self):
        return self._state


def test_palette_cards_leave_mouse_handling_to_the_card() -> None:
    app = QApplication.instance() or QApplication([])
    view = ManagementView(StubManagementController(_build_state()))

    palette_children = view._widget_palette.findChildren(QLabel)

    assert palette_children
    assert all(
        child.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        for child in palette_children
    )

    view.deleteLater()
    app.processEvents()


def test_empty_preview_cells_do_not_block_drop_target() -> None:
    app = QApplication.instance() or QApplication([])
    view = ManagementView(StubManagementController(_build_state()))

    empty_cells = view._layout_preview.findChildren(QLabel)
    click_to_place_labels = [
        cell for cell in empty_cells if cell.text() == "Place Widget"
    ]

    assert click_to_place_labels
    assert all(
        cell.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        for cell in click_to_place_labels
    )

    view.deleteLater()
    app.processEvents()


def _build_state() -> ManagementState:
    return ManagementState(
        screens=(
            Screen(
                screen_id="gaming",
                name="Gaming",
                availability=ScreenAvailability.AVAILABLE,
                layout=ScreenLayout(),
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
