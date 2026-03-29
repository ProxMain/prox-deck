from __future__ import annotations

from pathlib import Path

from proxdeck.domain.contracts.widget_discovery import WidgetDiscovery
from proxdeck.domain.exceptions.widget_discovery_errors import (
    WidgetDiscoveryLocationError,
    WidgetInstallMetadataError,
)
from proxdeck.domain.models.widget_manifest import WidgetManifest
from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.infrastructure.widgets.json_widget_manifest_loader import (
    JsonWidgetManifestLoader,
)
from proxdeck.infrastructure.widgets.widget_discovery_root import WidgetDiscoveryRoot


class FilesystemWidgetDiscovery(WidgetDiscovery):
    def __init__(
        self,
        roots: tuple[WidgetDiscoveryRoot, ...],
        loader: JsonWidgetManifestLoader,
    ) -> None:
        self._roots = roots
        self._loader = loader

    def discover_manifests(self) -> list[WidgetManifest]:
        manifests: list[WidgetManifest] = []
        for root in self._roots:
            if not root.path.exists():
                continue
            for manifest_path in sorted(root.path.glob("*/manifest.json")):
                manifest = self._loader.load(manifest_path)
                self._validate_root_kind(manifest, root)
                self._validate_install_metadata(manifest)
                manifests.append(manifest)
        return manifests

    def _validate_root_kind(
        self,
        manifest: WidgetManifest,
        root: WidgetDiscoveryRoot,
    ) -> None:
        if manifest.kind is not root.expected_kind:
            raise WidgetDiscoveryLocationError(
                widget_id=manifest.widget_id,
                expected_kind=root.expected_kind.value,
                actual_kind=manifest.kind.value,
            )

    def _validate_install_metadata(self, manifest: WidgetManifest) -> None:
        metadata = manifest.install_metadata
        if manifest.kind is WidgetKind.BUILTIN:
            if metadata.distribution != "core" or metadata.installation_scope != "bundled":
                raise WidgetInstallMetadataError(
                    widget_id=manifest.widget_id,
                    reason="builtin widgets must use distribution 'core' and installation_scope 'bundled'",
                )
            return

        if metadata.distribution != "installer":
            raise WidgetInstallMetadataError(
                widget_id=manifest.widget_id,
                reason="installable widgets must use distribution 'installer'",
            )
        if metadata.installation_scope != "custom-directory":
            raise WidgetInstallMetadataError(
                widget_id=manifest.widget_id,
                reason="installable widgets must use installation_scope 'custom-directory'",
            )
