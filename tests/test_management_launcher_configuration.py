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
        self.saved_stream_deck_payload = None

    def load_management_state(self):
        return self._state

    def configure_launcher_widget(self, screen_id: str, instance_id: str, items):
        self.saved_launcher_payload = (screen_id, instance_id, items)
        return self._state.screens[0]

    def configure_stream_deck_widget(self, screen_id: str, instance_id: str, size_variant: str, buttons):
        self.saved_stream_deck_payload = (screen_id, instance_id, size_variant, buttons)
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


def test_management_view_loads_stream_deck_settings_for_selected_instance() -> None:
    app = QApplication.instance() or QApplication([])
    state = _build_stream_deck_management_state()
    controller = StubManagementController(state)
    view = ManagementView(controller)

    view._widget_instance_list.setCurrentRow(0)

    assert view._stream_deck_size_selector.currentData() == "2/6-tall"
    assert view._stream_deck_button_inputs[0]["label"].text() == "Browser"
    assert view._stream_deck_button_inputs[0]["icon"].currentData() == "asset:stream_deck_browser.svg"
    assert view._stream_deck_button_inputs[0]["target"].text() == "https://example.com"

    view.deleteLater()
    app.processEvents()


def test_management_view_saves_stream_deck_settings() -> None:
    app = QApplication.instance() or QApplication([])
    state = _build_stream_deck_management_state()
    controller = StubManagementController(state)
    view = ManagementView(controller)
    view._widget_instance_list.setCurrentRow(0)

    view._stream_deck_size_selector.setCurrentIndex(0)
    view._stream_deck_button_inputs[0]["label"].setText("Discord")
    for index in range(view._stream_deck_button_inputs[0]["icon"].count()):
        if view._stream_deck_button_inputs[0]["icon"].itemData(index) == "asset:stream_deck_chat.svg":
            view._stream_deck_button_inputs[0]["icon"].setCurrentIndex(index)
            break
    view._stream_deck_button_inputs[0]["target"].setText("discord.exe")
    view._stream_deck_button_inputs[0]["action_type"].setCurrentIndex(0)
    view._handle_save_stream_deck_settings()

    assert controller.saved_stream_deck_payload[0:3] == ("gaming", "stream-deck-1", "1/6")
    assert controller.saved_stream_deck_payload[3][0]["label"] == "Discord"
    assert controller.saved_stream_deck_payload[3][0]["icon"] == "asset:stream_deck_chat.svg"
    assert controller.saved_stream_deck_payload[3][0]["action_config"]["target"] == "discord.exe"

    view.deleteLater()
    app.processEvents()


def test_management_view_preserves_custom_stream_deck_icon_values() -> None:
    app = QApplication.instance() or QApplication([])
    state = _build_stream_deck_management_state(
        buttons=[
            {
                "id": "steam-game",
                "label": "Steam Game",
                "icon": r"C:\Steam\appcache\librarycache\123\library_600x900.jpg",
                "action_type": "launch",
                "action_config": {"target": "steam://rungameid/123"},
            }
        ]
    )
    controller = StubManagementController(state)
    view = ManagementView(controller)
    view._widget_instance_list.setCurrentRow(0)

    view._handle_save_stream_deck_settings()

    assert controller.saved_stream_deck_payload[3][0]["icon"] == (
        r"C:\Steam\appcache\librarycache\123\library_600x900.jpg"
    )

    view.deleteLater()
    app.processEvents()


def test_management_view_preserves_stream_deck_buttons_beyond_visible_editor_slots() -> None:
    app = QApplication.instance() or QApplication([])
    buttons = []
    for index in range(40):
        buttons.append(
            {
                "id": f"button-{index + 1}",
                "label": f"Button {index + 1}",
                "icon": "",
                "action_type": "launch",
                "action_config": {"target": f"app-{index + 1}.exe"},
            }
        )
    state = _build_stream_deck_management_state(buttons=buttons)
    controller = StubManagementController(state)
    view = ManagementView(controller)
    view._widget_instance_list.setCurrentRow(0)

    view._stream_deck_button_inputs[0]["label"].setText("Discord")
    view._handle_save_stream_deck_settings()

    assert controller.saved_stream_deck_payload[3][0]["label"] == "Discord"
    assert controller.saved_stream_deck_payload[3][39]["label"] == "Button 40"
    assert controller.saved_stream_deck_payload[3][39]["action_config"]["target"] == "app-40.exe"

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
        compatibility=WidgetCompatibility(minimum_app_version=AppVersion.parse("1.0.0")),
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


def _build_stream_deck_management_state(
    buttons: list[dict[str, object]] | None = None,
) -> ManagementState:
    stream_deck_buttons = buttons or [
        {
            "id": "browser",
            "label": "Browser",
            "icon": "asset:stream_deck_browser.svg",
            "action_type": "launch",
            "action_config": {"target": "https://example.com"},
        }
    ]
    screen = Screen(
        screen_id="gaming",
        name="Gaming",
        availability=ScreenAvailability.AVAILABLE,
        layout=ScreenLayout(
            widget_instances=(
                WidgetInstance(
                    instance_id="stream-deck-1",
                    widget_id="stream-deck",
                    screen_id="gaming",
                    placement=WidgetPlacement(column=0, row=0, width=1, height=2),
                    settings={
                        "size_variant": "2/6-tall",
                        "buttons": stream_deck_buttons,
                    },
                ),
            )
        ),
    )
    definition = WidgetDefinition(
        widget_id="stream-deck",
        display_name="Stream Deck",
        version="1.0.0",
        kind=WidgetKind.BUILTIN,
        compatibility=WidgetCompatibility(minimum_app_version=AppVersion.parse("1.0.0")),
        install_metadata=WidgetInstallMetadata(
            distribution="core",
            installation_scope="bundled",
        ),
        capabilities=CapabilitySet(frozenset({"process-launch", "settings-mutation"})),
        entrypoint="widgets.stream_deck",
    )
    return ManagementState(
        screens=(screen,),
        widget_definitions=(definition,),
    )
