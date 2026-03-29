from __future__ import annotations

from dataclasses import dataclass

from proxdeck.domain.models.widget_compatibility import WidgetCompatibility
from proxdeck.domain.models.widget_install_metadata import WidgetInstallMetadata
from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.domain.value_objects.capability_set import CapabilitySet


@dataclass(frozen=True)
class WidgetManifest:
    widget_id: str
    display_name: str
    version: str
    kind: WidgetKind
    compatibility: WidgetCompatibility
    install_metadata: WidgetInstallMetadata
    capabilities: CapabilitySet
    entrypoint: str
    supports_multiple_instances: bool = True
