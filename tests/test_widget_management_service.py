from pathlib import Path

from proxdeck.application.services.default_screen_factory import DefaultScreenFactory
from proxdeck.application.services.screen_service import ScreenService
from proxdeck.application.services.widget_management_service import WidgetManagementService
from proxdeck.domain.contracts.screen_repository import ScreenRepository
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.domain.policies.layout_policy import LayoutPolicy
from proxdeck.domain.policies.screen_availability_policy import ScreenAvailabilityPolicy
from proxdeck.domain.policies.widget_compatibility_policy import (
    WidgetCompatibilityPolicy,
)
from proxdeck.domain.policies.widget_placement_finder import WidgetPlacementFinder
from proxdeck.domain.value_objects.app_version import AppVersion
from proxdeck.infrastructure.widgets.discovered_widget_catalog import (
    DiscoveredWidgetCatalog,
)
from proxdeck.infrastructure.widgets.filesystem_widget_discovery import (
    FilesystemWidgetDiscovery,
)
from proxdeck.infrastructure.widgets.json_widget_manifest_loader import (
    JsonWidgetManifestLoader,
)
from proxdeck.infrastructure.widgets.widget_discovery_root import WidgetDiscoveryRoot


class InMemoryScreenRepository(ScreenRepository):
    def __init__(self) -> None:
        self.saved_screens: list[Screen] = []
        self.active_screen_id: str | None = None

    def list_screens(self) -> list[Screen]:
        return list(self.saved_screens)

    def get_active_screen_id(self) -> str | None:
        return self.active_screen_id

    def save_screens(self, screens: list[Screen]) -> None:
        self.saved_screens = list(screens)

    def save_active_screen_id(self, screen_id: str) -> None:
        self.active_screen_id = screen_id


def build_management_service() -> WidgetManagementService:
    project_root = Path(__file__).resolve().parent.parent
    widget_catalog = DiscoveredWidgetCatalog(
        widget_discovery=FilesystemWidgetDiscovery(
            roots=(
                WidgetDiscoveryRoot(
                    path=project_root / "widgets",
                    expected_kind=WidgetKind.BUILTIN,
                ),
                WidgetDiscoveryRoot(
                    path=project_root / "installable_widgets",
                    expected_kind=WidgetKind.INSTALLABLE,
                ),
            ),
            loader=JsonWidgetManifestLoader(),
        ),
        current_app_version=AppVersion.parse("1.0.0"),
        compatibility_policy=WidgetCompatibilityPolicy(),
    )
    layout_policy = LayoutPolicy()
    screen_service = ScreenService(
        screen_repository=InMemoryScreenRepository(),
        widget_catalog=widget_catalog,
        default_screen_factory=DefaultScreenFactory(),
        layout_policy=layout_policy,
        availability_policy=ScreenAvailabilityPolicy(),
    )
    return WidgetManagementService(
        screen_service=screen_service,
        widget_catalog=widget_catalog,
        widget_placement_finder=WidgetPlacementFinder(layout_policy),
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


def test_management_service_builds_default_launcher_items() -> None:
    service = build_management_service()

    screen = service.add_widget_instance(
        screen_id="gaming",
        widget_id="launcher",
        column=0,
        row=0,
        width=1,
        height=1,
    )

    settings = screen.layout.widget_instances[0].settings
    assert settings["items"][0]["label"] == "GitHub"
    assert settings["items"][3]["target"] == "ms-settings:"


def test_management_service_updates_launcher_items() -> None:
    service = build_management_service()
    screen = service.add_widget_instance(
        screen_id="gaming",
        widget_id="launcher",
        column=0,
        row=0,
        width=1,
        height=1,
    )
    instance_id = screen.layout.widget_instances[0].instance_id

    updated = service.configure_launcher_widget(
        screen_id="gaming",
        instance_id=instance_id,
        items=[
            {"label": "Docs", "target": "https://example.com/docs"},
            {"label": "Mail", "target": "mailto:test@example.com"},
        ],
    )

    settings = updated.layout.widget_instances[0].settings
    assert settings["items"] == [
        {"label": "Docs", "target": "https://example.com/docs"},
        {"label": "Mail", "target": "mailto:test@example.com"},
    ]


def test_management_service_updates_widget_placement() -> None:
    service = build_management_service()
    screen = service.add_widget_instance(
        screen_id="gaming",
        widget_id="clock",
        column=0,
        row=0,
        width=1,
        height=1,
    )
    instance_id = screen.layout.widget_instances[0].instance_id

    updated = service.update_widget_instance_placement(
        screen_id="gaming",
        instance_id=instance_id,
        column=2,
        row=1,
        width=1,
        height=1,
    )

    placement = updated.layout.widget_instances[0].placement
    assert (placement.column, placement.row, placement.width, placement.height) == (2, 1, 1, 1)


def test_management_service_rejects_overlapping_widget_placement_update() -> None:
    service = build_management_service()
    first = service.add_widget_instance(
        screen_id="gaming",
        widget_id="clock",
        column=0,
        row=0,
        width=1,
        height=1,
    )
    service.add_widget_instance(
        screen_id="gaming",
        widget_id="notes",
        column=1,
        row=0,
        width=1,
        height=1,
    )
    instance_id = first.layout.widget_instances[0].instance_id

    try:
        service.update_widget_instance_placement(
            screen_id="gaming",
            instance_id=instance_id,
            column=1,
            row=0,
            width=1,
            height=1,
        )
    except ValueError as error:
        assert "overlaps" in str(error).lower()
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected overlapping placement update to be rejected")


def test_management_service_adds_widget_near_requested_cell_when_slot_is_free() -> None:
    service = build_management_service()

    screen = service.add_widget_instance_smart(
        screen_id="gaming",
        widget_id="clock",
        preferred_column=2,
        preferred_row=1,
    )

    placement = screen.layout.widget_instances[0].placement
    assert (placement.column, placement.row) == (2, 1)


def test_management_service_adds_widget_to_nearest_available_slot_when_requested_cell_is_taken() -> None:
    service = build_management_service()
    service.add_widget_instance(
        screen_id="gaming",
        widget_id="notes",
        column=2,
        row=1,
        width=1,
        height=1,
    )

    screen = service.add_widget_instance_smart(
        screen_id="gaming",
        widget_id="clock",
        preferred_column=2,
        preferred_row=1,
    )

    placement = next(
        instance.placement for instance in screen.layout.widget_instances if instance.widget_id == "clock"
    )
    assert (placement.column, placement.row) in {(1, 1), (2, 0)}


def test_management_service_moves_widget_to_nearest_valid_slot() -> None:
    service = build_management_service()
    first = service.add_widget_instance(
        screen_id="gaming",
        widget_id="clock",
        column=0,
        row=0,
        width=1,
        height=1,
    )
    service.add_widget_instance(
        screen_id="gaming",
        widget_id="notes",
        column=1,
        row=0,
        width=1,
        height=1,
    )

    updated = service.move_widget_instance_smart(
        screen_id="gaming",
        instance_id=first.layout.widget_instances[0].instance_id,
        preferred_column=1,
        preferred_row=0,
    )

    placement = next(
        instance.placement
        for instance in updated.layout.widget_instances
        if instance.widget_id == "clock"
    )
    assert (placement.column, placement.row) in {(0, 0), (2, 0), (1, 1)}


def test_management_service_resizes_widget_and_rehomes_it_when_needed() -> None:
    service = build_management_service()
    screen = service.add_widget_instance(
        screen_id="gaming",
        widget_id="clock",
        column=2,
        row=0,
        width=1,
        height=1,
    )
    instance_id = screen.layout.widget_instances[0].instance_id

    updated = service.resize_widget_instance_smart(
        screen_id="gaming",
        instance_id=instance_id,
        size_preset="2/6-wide",
    )

    placement = updated.layout.widget_instances[0].placement
    assert (placement.width, placement.height) == (2, 1)
    assert (placement.column, placement.row) == (1, 0)
