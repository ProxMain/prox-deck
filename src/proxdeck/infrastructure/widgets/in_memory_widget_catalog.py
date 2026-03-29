from __future__ import annotations

from proxdeck.domain.contracts.widget_catalog import WidgetCatalog
from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.domain.value_objects.capability_set import CapabilitySet


class InMemoryWidgetCatalog(WidgetCatalog):
    def __init__(self) -> None:
        definitions = [
            WidgetDefinition(
                widget_id="clock",
                display_name="Clock",
                version="1.0.0",
                kind=WidgetKind.BUILTIN,
                capabilities=CapabilitySet(),
                entrypoint="widgets.clock",
            ),
            WidgetDefinition(
                widget_id="launcher",
                display_name="Launcher",
                version="1.0.0",
                kind=WidgetKind.BUILTIN,
                capabilities=CapabilitySet(values=frozenset({"process-launch"})),
                entrypoint="widgets.launcher",
            ),
            WidgetDefinition(
                widget_id="notes",
                display_name="Notes",
                version="1.0.0",
                kind=WidgetKind.BUILTIN,
                capabilities=CapabilitySet(values=frozenset({"filesystem"})),
                entrypoint="widgets.notes",
            ),
            WidgetDefinition(
                widget_id="system-stats",
                display_name="System Stats",
                version="1.0.0",
                kind=WidgetKind.BUILTIN,
                capabilities=CapabilitySet(values=frozenset({"system-info"})),
                entrypoint="widgets.system_stats",
            ),
            WidgetDefinition(
                widget_id="web",
                display_name="Web Widget",
                version="1.0.0",
                kind=WidgetKind.BUILTIN,
                capabilities=CapabilitySet(values=frozenset({"network"})),
                entrypoint="widgets.web",
            ),
            WidgetDefinition(
                widget_id="media-controls",
                display_name="Media Controls",
                version="1.0.0",
                kind=WidgetKind.BUILTIN,
                capabilities=CapabilitySet(values=frozenset({"system-info"})),
                entrypoint="widgets.media_controls",
            ),
        ]
        self._definitions = {definition.widget_id: definition for definition in definitions}

    def list_widget_definitions(self) -> list[WidgetDefinition]:
        return list(self._definitions.values())

    def get_widget_definition(self, widget_id: str) -> WidgetDefinition:
        try:
            return self._definitions[widget_id]
        except KeyError as error:
            raise ValueError(f"Unknown widget definition: {widget_id}") from error
