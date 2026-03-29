from pathlib import Path

from proxdeck.domain.policies.widget_compatibility_policy import (
    WidgetCompatibilityPolicy,
)
from proxdeck.domain.models.widget_kind import WidgetKind
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
from proxdeck.infrastructure.widgets.widget_discovery_root import WidgetDiscoveryRoot
from proxdeck.presentation.widgets.widget_host_factory import WidgetHostFactory


def test_discovered_definition_exposes_install_metadata() -> None:
    project_root = Path(__file__).resolve().parent.parent
    catalog = DiscoveredWidgetCatalog(
        widget_discovery=FilesystemWidgetDiscovery(
            roots=(
                WidgetDiscoveryRoot(
                    path=project_root / "widgets",
                    expected_kind=WidgetKind.BUILTIN,
                ),
                WidgetDiscoveryRoot(
                    path=project_root / "installable_widgets",
                    expected_kind=WidgetKind.INSTALLABLE,
                ),
            ),
            loader=JsonWidgetManifestLoader(),
        ),
        current_app_version=AppVersion.parse("1.0.0"),
        compatibility_policy=WidgetCompatibilityPolicy(),
    )

    definition = catalog.get_widget_definition("web")

    assert definition.install_metadata.distribution == "core"
    assert definition.install_metadata.installation_scope == "bundled"
    assert str(definition.compatibility.minimum_app_version) == "1.0.0"


def test_discovered_definition_exposes_installable_widget_metadata() -> None:
    project_root = Path(__file__).resolve().parent.parent
    catalog = DiscoveredWidgetCatalog(
        widget_discovery=FilesystemWidgetDiscovery(
            roots=(
                WidgetDiscoveryRoot(
                    path=project_root / "widgets",
                    expected_kind=WidgetKind.BUILTIN,
                ),
                WidgetDiscoveryRoot(
                    path=project_root / "installable_widgets",
                    expected_kind=WidgetKind.INSTALLABLE,
                ),
            ),
            loader=JsonWidgetManifestLoader(),
        ),
        current_app_version=AppVersion.parse("1.0.0"),
        compatibility_policy=WidgetCompatibilityPolicy(),
    )

    definition = catalog.get_widget_definition("community-browser")

    assert definition.kind is WidgetKind.INSTALLABLE
    assert definition.install_metadata.distribution == "installer"
    assert definition.install_metadata.installation_scope == "custom-directory"
    assert definition.capabilities.requires("network")


def test_widget_host_factory_formats_metadata_footer() -> None:
    project_root = Path(__file__).resolve().parent.parent
    catalog = DiscoveredWidgetCatalog(
        widget_discovery=FilesystemWidgetDiscovery(
            roots=(
                WidgetDiscoveryRoot(
                    path=project_root / "widgets",
                    expected_kind=WidgetKind.BUILTIN,
                ),
                WidgetDiscoveryRoot(
                    path=project_root / "installable_widgets",
                    expected_kind=WidgetKind.INSTALLABLE,
                ),
            ),
            loader=JsonWidgetManifestLoader(),
        ),
        current_app_version=AppVersion.parse("1.0.0"),
        compatibility_policy=WidgetCompatibilityPolicy(),
    )

    definition = catalog.get_widget_definition("web")
    footer = WidgetHostFactory()._build_metadata_footer(definition)

    assert "Kind: builtin" in footer
    assert "Min app: 1.0.0" in footer
    assert "Distribution: core" in footer
    assert "Scope: bundled" in footer
    assert "Capabilities: network" in footer
