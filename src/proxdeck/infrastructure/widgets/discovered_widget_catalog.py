from __future__ import annotations

from proxdeck.domain.contracts.widget_catalog import WidgetCatalog
from proxdeck.domain.contracts.widget_discovery import WidgetDiscovery
from proxdeck.domain.exceptions.widget_discovery_errors import DuplicateWidgetIdError
from proxdeck.domain.models.widget_definition import WidgetDefinition


class DiscoveredWidgetCatalog(WidgetCatalog):
    def __init__(self, widget_discovery: WidgetDiscovery) -> None:
        definitions: dict[str, WidgetDefinition] = {}
        for manifest in widget_discovery.discover_manifests():
            if manifest.widget_id in definitions:
                raise DuplicateWidgetIdError(manifest.widget_id)

            definitions[manifest.widget_id] = WidgetDefinition(
                widget_id=manifest.widget_id,
                display_name=manifest.display_name,
                version=manifest.version,
                kind=manifest.kind,
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
