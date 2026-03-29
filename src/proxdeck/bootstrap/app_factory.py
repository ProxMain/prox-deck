from __future__ import annotations

from pathlib import Path

from proxdeck.application.controllers.management_controller import ManagementController
from proxdeck.application.controllers.runtime_controller import RuntimeController
from proxdeck.application.services.default_screen_factory import DefaultScreenFactory
from proxdeck.application.services.runtime_startup_service import RuntimeStartupService
from proxdeck.application.services.screen_service import ScreenService
from proxdeck.application.services.widget_management_service import WidgetManagementService
from proxdeck.bootstrap.settings import APP_VERSION, AppPaths, build_app_paths
from proxdeck.domain.policies.layout_policy import LayoutPolicy
from proxdeck.domain.policies.screen_availability_policy import ScreenAvailabilityPolicy
from proxdeck.domain.policies.widget_compatibility_policy import (
    WidgetCompatibilityPolicy,
)
from proxdeck.infrastructure.persistence.json_screen_repository import JsonScreenRepository
from proxdeck.infrastructure.system.resolution_runtime_target_detector import (
    ResolutionRuntimeTargetDetector,
)
from proxdeck.infrastructure.widgets.discovered_widget_catalog import (
    DiscoveredWidgetCatalog,
)
from proxdeck.infrastructure.widgets.filesystem_widget_discovery import (
    FilesystemWidgetDiscovery,
)
from proxdeck.infrastructure.widgets.json_widget_manifest_loader import (
    JsonWidgetManifestLoader,
)
from proxdeck.presentation.app import ProxDeckApplication


class AppFactory:
    def __init__(self, project_root: Path) -> None:
        self._paths = build_app_paths(project_root)

    @property
    def paths(self) -> AppPaths:
        return self._paths

    def create(self) -> ProxDeckApplication:
        screen_repository = JsonScreenRepository(self._paths.screen_state_path)
        widget_catalog = DiscoveredWidgetCatalog(
            widget_discovery=FilesystemWidgetDiscovery(
                roots=(
                    self._paths.builtin_widgets_root,
                    self._paths.installable_widgets_root,
                ),
                loader=JsonWidgetManifestLoader(),
            ),
            current_app_version=APP_VERSION,
            compatibility_policy=WidgetCompatibilityPolicy(),
        )
        screen_service = ScreenService(
            screen_repository=screen_repository,
            widget_catalog=widget_catalog,
            default_screen_factory=DefaultScreenFactory(),
            layout_policy=LayoutPolicy(),
            availability_policy=ScreenAvailabilityPolicy(),
        )
        runtime_controller = RuntimeController(
            runtime_startup_service=RuntimeStartupService(
                screen_service=screen_service,
                runtime_target_detector=ResolutionRuntimeTargetDetector(),
            ),
            screen_service=screen_service,
        )
        management_controller = ManagementController(
            widget_management_service=WidgetManagementService(
                screen_service=screen_service,
                widget_catalog=widget_catalog,
            )
        )
        return ProxDeckApplication(
            runtime_controller=runtime_controller,
            management_controller=management_controller,
        )
