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
        self.saved_launcher_payload = None

    def load_management_state(self):
        return self._state

    def configure_launcher_widget(self, screen_id: str, instance_id: str, items):
        self.saved_launcher_payload = (screen_id, instance_id, items)
        return self._state.screens[0]


def test_management_view_loads_launcher_settings_for_selected_instance() -> None:
    app = QApplication.instance() or QApplication([])
    state = _build_launcher_management_state()
    controller = StubManagementController(state)
    view = ManagementView(controller)

    view._widget_instance_list.setCurrentRow(0)

    assert view._launcher_label_inputs[0].text() == "Docs"
    assert view._launcher_target_inputs[0].text() == "https://example.com/docs"
    assert view._launcher_label_inputs[1].text() == "Mail"

    view.deleteLater()
    app.processEvents()


def test_management_view_saves_launcher_settings() -> None:
    app = QApplication.instance() or QApplication([])
    state = _build_launcher_management_state()
    controller = StubManagementController(state)
    view = ManagementView(controller)
    view._widget_instance_list.setCurrentRow(0)

    view._launcher_label_inputs[0].setText("GitLab")
    view._launcher_target_inputs[0].setText("https://gitlab.com")
    view._launcher_label_inputs[1].setText("Mail")
    view._launcher_target_inputs[1].setText("mailto:test@example.com")
    view._handle_save_launcher_settings()

    assert controller.saved_launcher_payload == (
        "gaming",
        "launcher-1",
        [
            {"label": "GitLab", "target": "https://gitlab.com"},
            {"label": "Mail", "target": "mailto:test@example.com"},
            {"label": "", "target": ""},
            {"label": "", "target": ""},
        ],
    )

    view.deleteLater()
    app.processEvents()


def _build_launcher_management_state() -> ManagementState:
    screen = Screen(
        screen_id="gaming",
        name="Gaming",
        availability=ScreenAvailability.AVAILABLE,
        layout=ScreenLayout(
            widget_instances=(
                WidgetInstance(
                    instance_id="launcher-1",
                    widget_id="launcher",
                    screen_id="gaming",
                    placement=WidgetPlacement(column=0, row=0, width=1, height=1),
                    settings={
                        "items": [
                            {"label": "Docs", "target": "https://example.com/docs"},
                            {"label": "Mail", "target": "mailto:test@example.com"},
                        ]
                    },
                ),
            )
        ),
    )
    definition = WidgetDefinition(
        widget_id="launcher",
        display_name="Launcher",
        version="1.0.0",
        kind=WidgetKind.BUILTIN,
        compatibility=WidgetCompatibility(minimum_app_version=AppVersion.parse("0.1.0")),
        install_metadata=WidgetInstallMetadata(
            distribution="core",
            installation_scope="bundled",
        ),
        capabilities=CapabilitySet(frozenset({"process-launch"})),
        entrypoint="widgets.launcher",
    )
    return ManagementState(
        screens=(screen,),
        widget_definitions=(definition,),
    )
