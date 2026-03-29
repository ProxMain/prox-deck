from proxdeck.application.services.default_screen_factory import DefaultScreenFactory
from proxdeck.application.services.screen_service import ScreenService
from proxdeck.application.services.widget_management_service import WidgetManagementService
from proxdeck.domain.contracts.screen_repository import ScreenRepository
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.domain.policies.layout_policy import LayoutPolicy
from proxdeck.domain.policies.screen_availability_policy import ScreenAvailabilityPolicy
from proxdeck.domain.policies.widget_compatibility_policy import (
    WidgetCompatibilityPolicy,
)
from proxdeck.domain.policies.widget_placement_finder import WidgetPlacementFinder
from proxdeck.domain.value_objects.app_version import AppVersion
from proxdeck.domain.value_objects.widget_placement import WidgetPlacement
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
    from pathlib import Path

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
        current_app_version=AppVersion.parse("0.1.0"),
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


def test_widget_management_service_suggests_first_available_slot() -> None:
    service = build_management_service()

    placement = service.suggest_placement(
        screen_id="gaming",
        widget_id="clock",
        width=1,
        height=1,
    )

    assert placement is not None
    assert placement.column == 0
    assert placement.row == 0


def test_widget_management_service_skips_occupied_slots() -> None:
    service = build_management_service()
    service.add_widget_instance(
        screen_id="gaming",
        widget_id="clock",
        column=0,
        row=0,
        width=1,
        height=1,
    )

    placement = service.suggest_placement(
        screen_id="gaming",
        widget_id="notes",
        width=1,
        height=1,
    )

    assert placement is not None
    assert (placement.column, placement.row) == (1, 0)


def test_widget_management_service_returns_none_when_no_slot_fits() -> None:
    service = build_management_service()
    service.add_widget_instance(
        screen_id="gaming",
        widget_id="web",
        column=0,
        row=0,
        width=3,
        height=2,
    )

    placement = service.suggest_placement(
        screen_id="gaming",
        widget_id="clock",
        width=1,
        height=1,
    )

    assert placement is None
