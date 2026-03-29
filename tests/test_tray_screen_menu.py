from pathlib import Path

from proxdeck.application.dto.runtime_state import RuntimeState
from proxdeck.application.services.default_screen_factory import DefaultScreenFactory
from proxdeck.application.services.screen_service import ScreenService
from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.domain.policies.layout_policy import LayoutPolicy
from proxdeck.domain.policies.screen_availability_policy import ScreenAvailabilityPolicy
from proxdeck.domain.policies.widget_compatibility_policy import (
    WidgetCompatibilityPolicy,
)
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
from proxdeck.presentation.app import ProxDeckApplication
from tests.test_screen_service import InMemoryScreenRepository


def test_tray_screen_menu_entries_mark_active_and_locked_screens() -> None:
    repository = InMemoryScreenRepository()
    service = ScreenService(
        screen_repository=repository,
        widget_catalog=_build_widget_catalog(),
        default_screen_factory=DefaultScreenFactory(),
        layout_policy=LayoutPolicy(),
        availability_policy=ScreenAvailabilityPolicy(),
    )
    screens = tuple(service.list_screens())
    runtime_state = RuntimeState(
        active_screen=screens[1],
        available_screens=screens,
        runtime_target=None,
    )

    entries = ProxDeckApplication._build_screen_menu_entries(runtime_state)

    assert entries[0] == {
        "screen_id": "gaming",
        "label": "Gaming",
        "enabled": True,
        "checked": False,
    }
    assert entries[1] == {
        "screen_id": "performance",
        "label": "Performance",
        "enabled": True,
        "checked": True,
    }
    assert entries[3] == {
        "screen_id": "developing",
        "label": "Developing (Soon)",
        "enabled": False,
        "checked": False,
    }


def _build_widget_catalog() -> DiscoveredWidgetCatalog:
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
        current_app_version=AppVersion.parse("0.1.0"),
        compatibility_policy=WidgetCompatibilityPolicy(),
    )
