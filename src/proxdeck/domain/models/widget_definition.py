from __future__ import annotations

from dataclasses import dataclass

from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.domain.value_objects.capability_set import CapabilitySet


@dataclass(frozen=True)
class WidgetDefinition:
    widget_id: str
    display_name: str
    version: str
    kind: WidgetKind
    capabilities: CapabilitySet
    entrypoint: str
    supports_multiple_instances: bool = True
