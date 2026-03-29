from pathlib import Path

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
