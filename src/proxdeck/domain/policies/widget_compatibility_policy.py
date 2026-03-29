from __future__ import annotations

from proxdeck.domain.exceptions.widget_discovery_errors import IncompatibleWidgetError
from proxdeck.domain.models.widget_manifest import WidgetManifest
from proxdeck.domain.value_objects.app_version import AppVersion


class WidgetCompatibilityPolicy:
    def ensure_supported(
        self,
        manifest: WidgetManifest,
        current_app_version: AppVersion,
    ) -> None:
        if manifest.compatibility.minimum_app_version > current_app_version:
            raise IncompatibleWidgetError(
                widget_id=manifest.widget_id,
                required_version=str(manifest.compatibility.minimum_app_version),
                current_version=str(current_app_version),
            )
