from proxdeck.application.services.default_screen_factory import DefaultScreenFactory
from proxdeck.application.services.screen_service import ScreenService
from proxdeck.application.services.widget_management_service import WidgetManagementService
from proxdeck.domain.contracts.screen_repository import ScreenRepository
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.policies.layout_policy import LayoutPolicy
from proxdeck.domain.policies.screen_availability_policy import ScreenAvailabilityPolicy
from proxdeck.infrastructure.widgets.in_memory_widget_catalog import InMemoryWidgetCatalog


class InMemoryScreenRepository(ScreenRepository):
    def __init__(self) -> None:
        self.saved_screens: list[Screen] = []

    def list_screens(self) -> list[Screen]:
        return list(self.saved_screens)

    def save_screens(self, screens: list[Screen]) -> None:
        self.saved_screens = list(screens)


def build_management_service() -> WidgetManagementService:
    screen_service = ScreenService(
        screen_repository=InMemoryScreenRepository(),
        widget_catalog=InMemoryWidgetCatalog(),
        default_screen_factory=DefaultScreenFactory(),
        layout_policy=LayoutPolicy(),
        availability_policy=ScreenAvailabilityPolicy(),
    )
    return WidgetManagementService(
        screen_service=screen_service,
        widget_catalog=InMemoryWidgetCatalog(),
    )


def test_management_service_adds_widget_instance() -> None:
    service = build_management_service()

    screen = service.add_widget_instance(
        screen_id="gaming",
        widget_id="clock",
        column=0,
        row=0,
        width=1,
        height=1,
    )

    assert len(screen.layout.widget_instances) == 1
    assert screen.layout.widget_instances[0].widget_id == "clock"


def test_management_service_updates_web_widget_settings() -> None:
    service = build_management_service()
    screen = service.add_widget_instance(
        screen_id="gaming",
        widget_id="web",
        column=0,
        row=0,
        width=2,
        height=1,
    )
    instance_id = screen.layout.widget_instances[0].instance_id

    updated = service.configure_web_widget(
        screen_id="gaming",
        instance_id=instance_id,
        url="https://openai.com",
        force_mobile=True,
    )

    settings = updated.layout.widget_instances[0].settings
    assert settings["url"] == "https://openai.com"
    assert settings["force_mobile"] is True


def test_management_state_lists_builtin_widgets() -> None:
    service = build_management_service()

    state = service.load_management_state()

    widget_ids = {item.widget_id for item in state.widget_definitions}
    assert {"clock", "launcher", "notes", "system-stats", "web", "media-controls"} <= widget_ids
