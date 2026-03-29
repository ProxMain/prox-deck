from __future__ import annotations

from abc import ABC, abstractmethod

from proxdeck.domain.models.widget_manifest import WidgetManifest


class WidgetDiscovery(ABC):
    @abstractmethod
    def discover_manifests(self) -> list[WidgetManifest]:
        raise NotImplementedError
