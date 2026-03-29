from __future__ import annotations

import json
from pathlib import Path

from proxdeck.domain.exceptions.widget_discovery_errors import WidgetManifestLoadError
from proxdeck.domain.models.widget_compatibility import WidgetCompatibility
from proxdeck.domain.models.widget_install_metadata import WidgetInstallMetadata
from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.domain.models.widget_manifest import WidgetManifest
from proxdeck.domain.value_objects.app_version import AppVersion
from proxdeck.domain.value_objects.capability_set import CapabilitySet


class JsonWidgetManifestLoader:
    def load(self, manifest_path: Path) -> WidgetManifest:
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            return WidgetManifest(
                widget_id=str(payload["widget_id"]),
                display_name=str(payload["display_name"]),
                version=str(payload["version"]),
                kind=WidgetKind(str(payload["kind"])),
                compatibility=WidgetCompatibility(
                    minimum_app_version=AppVersion.parse(
                        str(payload["compatibility"]["minimum_app_version"])
                    )
                ),
                install_metadata=WidgetInstallMetadata(
                    distribution=str(payload["install_metadata"]["distribution"]),
                    installation_scope=str(
                        payload["install_metadata"]["installation_scope"]
                    ),
                ),
                capabilities=CapabilitySet(
                    values=frozenset(payload.get("capabilities", []))
                ),
                entrypoint=str(payload["entrypoint"]),
                supports_multiple_instances=bool(
                    payload.get("supports_multiple_instances", True)
                ),
            )
        except FileNotFoundError as error:
            raise WidgetManifestLoadError(manifest_path, "file does not exist") from error
        except json.JSONDecodeError as error:
            raise WidgetManifestLoadError(manifest_path, "invalid JSON") from error
        except KeyError as error:
            raise WidgetManifestLoadError(
                manifest_path,
                f"missing required field: {error.args[0]}",
            ) from error
        except ValueError as error:
            raise WidgetManifestLoadError(manifest_path, str(error)) from error
