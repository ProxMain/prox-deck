from pathlib import Path

from proxdeck.domain.policies.widget_compatibility_policy import (
    WidgetCompatibilityPolicy,
)
from proxdeck.domain.value_objects.app_version import AppVersion
from proxdeck.infrastructure.widgets.discovered_widget_catalog import (
    DiscoveredWidgetCatalog,
)
from proxdeck.infrastructure.widgets.filesystem_widget_discovery import (
    FilesystemWidgetDiscovery,
)
from proxdeck.infrastructure.widgets.json_widget_manifest_loader import (
    JsonWidgetManifestLoader,
)
from proxdeck.presentation.widgets.widget_host_factory import WidgetHostFactory


def test_discovered_definition_exposes_install_metadata() -> None:
    project_root = Path(__file__).resolve().parent.parent
    catalog = DiscoveredWidgetCatalog(
        widget_discovery=FilesystemWidgetDiscovery(
            roots=(project_root / "widgets", project_root / "installable_widgets"),
            loader=JsonWidgetManifestLoader(),
        ),
        current_app_version=AppVersion.parse("0.1.0"),
        compatibility_policy=WidgetCompatibilityPolicy(),
    )

    definition = catalog.get_widget_definition("web")

    assert definition.install_metadata.distribution == "core"
    assert definition.install_metadata.installation_scope == "bundled"
    assert str(definition.compatibility.minimum_app_version) == "0.1.0"


def test_widget_host_factory_formats_metadata_footer() -> None:
    project_root = Path(__file__).resolve().parent.parent
    catalog = DiscoveredWidgetCatalog(
        widget_discovery=FilesystemWidgetDiscovery(
            roots=(project_root / "widgets", project_root / "installable_widgets"),
            loader=JsonWidgetManifestLoader(),
        ),
        current_app_version=AppVersion.parse("0.1.0"),
        compatibility_policy=WidgetCompatibilityPolicy(),
    )

    definition = catalog.get_widget_definition("web")
    footer = WidgetHostFactory()._build_metadata_footer(definition)

    assert "Kind: builtin" in footer
    assert "Min app: 0.1.0" in footer
    assert "Distribution: core" in footer
    assert "Scope: bundled" in footer
    assert "Capabilities: network" in footer
