from __future__ import annotations

from proxdeck.domain.contracts.widget_catalog import WidgetCatalog
from proxdeck.domain.contracts.widget_discovery import WidgetDiscovery
from proxdeck.domain.exceptions.widget_discovery_errors import DuplicateWidgetIdError
from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.policies.widget_compatibility_policy import WidgetCompatibilityPolicy
from proxdeck.domain.value_objects.app_version import AppVersion


class DiscoveredWidgetCatalog(WidgetCatalog):
    def __init__(
        self,
        widget_discovery: WidgetDiscovery,
        current_app_version: AppVersion,
        compatibility_policy: WidgetCompatibilityPolicy,
    ) -> None:
        definitions: dict[str, WidgetDefinition] = {}
        for manifest in widget_discovery.discover_manifests():
            if manifest.widget_id in definitions:
                raise DuplicateWidgetIdError(manifest.widget_id)
            compatibility_policy.ensure_supported(manifest, current_app_version)

            definitions[manifest.widget_id] = WidgetDefinition(
                widget_id=manifest.widget_id,
                display_name=manifest.display_name,
                version=manifest.version,
                kind=manifest.kind,
                compatibility=manifest.compatibility,
                install_metadata=manifest.install_metadata,
                capabilities=manifest.capabilities,
                entrypoint=manifest.entrypoint,
                supports_multiple_instances=manifest.supports_multiple_instances,
            )
        self._definitions = definitions

    def list_widget_definitions(self) -> list[WidgetDefinition]:
        return list(self._definitions.values())

    def get_widget_definition(self, widget_id: str) -> WidgetDefinition:
        try:
            return self._definitions[widget_id]
        except KeyError as error:
            raise ValueError(f"Unknown widget definition: {widget_id}") from error
