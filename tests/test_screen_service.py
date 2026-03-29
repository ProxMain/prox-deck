from pathlib import Path

from proxdeck.application.services.default_screen_factory import DefaultScreenFactory
from proxdeck.application.services.screen_service import ScreenService
from proxdeck.domain.contracts.screen_repository import ScreenRepository
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.screen_availability import ScreenAvailability
from proxdeck.domain.models.screen_layout import ScreenLayout
from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.domain.policies.widget_compatibility_policy import (
    WidgetCompatibilityPolicy,
)
from proxdeck.domain.value_objects.app_version import AppVersion
from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.domain.policies.layout_policy import LayoutPolicy
from proxdeck.domain.policies.screen_availability_policy import ScreenAvailabilityPolicy
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


def build_widget_catalog() -> DiscoveredWidgetCatalog:
    project_root = Path(__file__).resolve().parent.parent
    return DiscoveredWidgetCatalog(
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


def test_screen_service_bootstraps_default_screens() -> None:
    service = ScreenService(
        screen_repository=InMemoryScreenRepository(),
        widget_catalog=build_widget_catalog(),
        default_screen_factory=DefaultScreenFactory(),
        layout_policy=LayoutPolicy(),
        availability_policy=ScreenAvailabilityPolicy(),
    )

    screens = service.list_screens()

    assert [screen.screen_id for screen in screens] == [
        "gaming",
        "performance",
        "streaming",
        "developing",
    ]


def test_screen_service_persists_widget_addition() -> None:
    repository = InMemoryScreenRepository()
    repository.save_screens(
        [
            Screen(
                screen_id="gaming",
                name="Gaming",
                availability=ScreenAvailability.AVAILABLE,
                layout=ScreenLayout(),
            )
        ]
    )
    repository.save_active_screen_id("gaming")
    service = ScreenService(
        screen_repository=repository,
        widget_catalog=build_widget_catalog(),
        default_screen_factory=DefaultScreenFactory(),
        layout_policy=LayoutPolicy(),
        availability_policy=ScreenAvailabilityPolicy(),
    )

    widget_instance = WidgetInstance(
        instance_id="clock-1",
        widget_id="clock",
        screen_id="gaming",
        placement=WidgetPlacement(column=0, row=0, width=1, height=1),
    )

    updated = service.add_widget_instance("gaming", widget_instance)

    assert len(updated.layout.widget_instances) == 1
    assert repository.list_screens()[0].layout.widget_instances[0].widget_id == "clock"


def test_screen_service_restores_persisted_active_screen() -> None:
    repository = InMemoryScreenRepository()
    service = ScreenService(
        screen_repository=repository,
        widget_catalog=build_widget_catalog(),
        default_screen_factory=DefaultScreenFactory(),
        layout_policy=LayoutPolicy(),
        availability_policy=ScreenAvailabilityPolicy(),
    )
    service.list_screens()
    repository.save_active_screen_id("streaming")

    active_screen = service.get_active_screen()

    assert active_screen.screen_id == "streaming"


def test_screen_service_falls_back_when_persisted_screen_is_unavailable() -> None:
    repository = InMemoryScreenRepository()
    service = ScreenService(
        screen_repository=repository,
        widget_catalog=build_widget_catalog(),
        default_screen_factory=DefaultScreenFactory(),
        layout_policy=LayoutPolicy(),
        availability_policy=ScreenAvailabilityPolicy(),
    )
    service.list_screens()
    repository.save_active_screen_id("developing")

    active_screen = service.get_active_screen()

    assert active_screen.screen_id == "gaming"
    assert repository.get_active_screen_id() == "gaming"
