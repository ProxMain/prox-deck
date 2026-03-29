import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from proxdeck.application.dto.management_state import ManagementState
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.screen_availability import ScreenAvailability
from proxdeck.domain.models.screen_layout import ScreenLayout
from proxdeck.domain.models.widget_compatibility import WidgetCompatibility
from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_install_metadata import WidgetInstallMetadata
from proxdeck.domain.models.widget_kind import WidgetKind
from proxdeck.domain.value_objects.app_version import AppVersion
from proxdeck.domain.value_objects.capability_set import CapabilitySet
from proxdeck.presentation.views.management_view import ManagementView


class StubManagementController:
    def __init__(self, screens, widget_definitions) -> None:
        self._state = ManagementState(
            screens=tuple(screens),
            widget_definitions=tuple(widget_definitions),
        )

    def load_management_state(self):
        return self._state


def test_management_view_shows_low_risk_definition_summary() -> None:
    app = QApplication.instance() or QApplication([])
    view = ManagementView(
        StubManagementController(
            screens=[_build_screen()],
            widget_definitions=[
                _build_definition(
                    widget_id="clock",
                    display_name="Clock",
                    kind=WidgetKind.BUILTIN,
                    capabilities=frozenset(),
                    distribution="core",
                    installation_scope="bundled",
                )
            ],
        )
    )

    metadata = view._definition_metadata_label.text()

    assert "Capabilities: none" in metadata
    assert "Capability summary: No privileged capabilities requested." in metadata
    assert "Risk: Low. This widget runs without privileged capability access." in metadata

    view.deleteLater()
    app.processEvents()


def test_management_view_shows_elevated_risk_for_installable_widget() -> None:
    app = QApplication.instance() or QApplication([])
    view = ManagementView(
        StubManagementController(
            screens=[_build_screen()],
            widget_definitions=[
                _build_definition(
                    widget_id="community-browser",
                    display_name="Community Browser",
                    kind=WidgetKind.INSTALLABLE,
                    capabilities=frozenset({"network", "filesystem"}),
                    distribution="installer",
                    installation_scope="custom-directory",
                )
            ],
        )
    )

    metadata = view._definition_metadata_label.text()

    assert "Capabilities: filesystem, network" in metadata
    assert "Capability summary: Requests filesystem access, and network access." in metadata
    assert (
        "Risk: Elevated. This widget requests filesystem access, network access. "
        "Review carefully before enabling third-party code."
    ) in metadata

    view.deleteLater()
    app.processEvents()


def _build_screen() -> Screen:
    return Screen(
        screen_id="gaming",
        name="Gaming",
        availability=ScreenAvailability.AVAILABLE,
        layout=ScreenLayout(),
    )


def _build_definition(
    widget_id: str,
    display_name: str,
    kind: WidgetKind,
    capabilities: frozenset[str],
    distribution: str,
    installation_scope: str,
) -> WidgetDefinition:
    return WidgetDefinition(
        widget_id=widget_id,
        display_name=display_name,
        version="1.0.0",
        kind=kind,
        compatibility=WidgetCompatibility(
            minimum_app_version=AppVersion.parse("0.1.0")
        ),
        install_metadata=WidgetInstallMetadata(
            distribution=distribution,
            installation_scope=installation_scope,
        ),
        capabilities=CapabilitySet(capabilities),
        entrypoint=f"widgets.{widget_id}",
    )
