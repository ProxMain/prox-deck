from __future__ import annotations

import json
from pathlib import Path

from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.domain.models.widget_manifest import WidgetManifest
from proxdeck.domain.value_objects.capability_set import CapabilitySet


class JsonWidgetManifestLoader:
    def load(self, manifest_path: Path) -> WidgetManifest:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return WidgetManifest(
            widget_id=str(payload["widget_id"]),
            display_name=str(payload["display_name"]),
            version=str(payload["version"]),
            kind=WidgetKind(str(payload["kind"])),
            capabilities=CapabilitySet(
                values=frozenset(payload.get("capabilities", []))
            ),
            entrypoint=str(payload["entrypoint"]),
            supports_multiple_instances=bool(
                payload.get("supports_multiple_instances", True)
            ),
        )
