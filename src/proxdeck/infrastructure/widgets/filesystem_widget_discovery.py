from __future__ import annotations

from pathlib import Path

from proxdeck.domain.contracts.widget_discovery import WidgetDiscovery
from proxdeck.domain.models.widget_manifest import WidgetManifest
from proxdeck.infrastructure.widgets.json_widget_manifest_loader import (
    JsonWidgetManifestLoader,
)


class FilesystemWidgetDiscovery(WidgetDiscovery):
    def __init__(self, roots: tuple[Path, ...], loader: JsonWidgetManifestLoader) -> None:
        self._roots = roots
        self._loader = loader

    def discover_manifests(self) -> list[WidgetManifest]:
        manifests: list[WidgetManifest] = []
        for root in self._roots:
            if not root.exists():
                continue
            for manifest_path in sorted(root.glob("*/manifest.json")):
                manifests.append(self._loader.load(manifest_path))
        return manifests
