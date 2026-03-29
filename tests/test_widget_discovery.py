import json
import shutil
import uuid
from pathlib import Path

from proxdeck.domain.exceptions.widget_discovery_errors import (
    DuplicateWidgetIdError,
    WidgetManifestLoadError,
)
from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.infrastructure.widgets.discovered_widget_catalog import (
    DiscoveredWidgetCatalog,
)
from proxdeck.infrastructure.widgets.filesystem_widget_discovery import (
    FilesystemWidgetDiscovery,
)
from proxdeck.infrastructure.widgets.json_widget_manifest_loader import (
    JsonWidgetManifestLoader,
)


def test_manifest_loader_reads_builtin_widget_manifest() -> None:
    project_root = Path(__file__).resolve().parent.parent
    manifest = JsonWidgetManifestLoader().load(project_root / "widgets" / "web" / "manifest.json")

    assert manifest.widget_id == "web"
    assert manifest.kind is WidgetKind.BUILTIN
    assert manifest.capabilities.requires("network")


def test_discovery_catalog_loads_builtin_widget_manifests() -> None:
    project_root = Path(__file__).resolve().parent.parent
    catalog = DiscoveredWidgetCatalog(
        widget_discovery=FilesystemWidgetDiscovery(
            roots=(project_root / "widgets", project_root / "installable_widgets"),
            loader=JsonWidgetManifestLoader(),
        )
    )

    widget_ids = {item.widget_id for item in catalog.list_widget_definitions()}
    assert {"clock", "launcher", "notes", "system-stats", "web", "media-controls"} <= widget_ids


def test_manifest_loader_rejects_invalid_manifest() -> None:
    temp_root = build_temp_root()
    try:
        manifest_path = temp_root / "broken.json"
        manifest_path.write_text(json.dumps({"widget_id": "broken"}), encoding="utf-8")

        try:
            JsonWidgetManifestLoader().load(manifest_path)
        except WidgetManifestLoadError as error:
            assert "missing required field" in str(error)
            return

        raise AssertionError("Expected invalid manifest to be rejected")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def test_discovery_catalog_rejects_duplicate_widget_ids() -> None:
    temp_root = build_temp_root()
    try:
        first_root = temp_root / "widgets-one"
        second_root = temp_root / "widgets-two"
        (first_root / "clock").mkdir(parents=True)
        (second_root / "clock-copy").mkdir(parents=True)

        manifest_payload = {
            "widget_id": "clock",
            "display_name": "Clock",
            "version": "1.0.0",
            "kind": "builtin",
            "capabilities": [],
            "entrypoint": "widgets.clock",
            "supports_multiple_instances": True,
        }
        (first_root / "clock" / "manifest.json").write_text(
            json.dumps(manifest_payload),
            encoding="utf-8",
        )
        (second_root / "clock-copy" / "manifest.json").write_text(
            json.dumps({**manifest_payload, "display_name": "Clock Copy"}),
            encoding="utf-8",
        )

        try:
            DiscoveredWidgetCatalog(
                widget_discovery=FilesystemWidgetDiscovery(
                    roots=(first_root, second_root),
                    loader=JsonWidgetManifestLoader(),
                )
            )
        except DuplicateWidgetIdError as error:
            assert error.widget_id == "clock"
            return

        raise AssertionError("Expected duplicate widget ids to be rejected")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def build_temp_root() -> Path:
    root = Path.cwd() / ".test-artifacts" / f"widget-discovery-{uuid.uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=False)
    return root
