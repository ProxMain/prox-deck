from __future__ import annotations

from collections.abc import Callable

from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.application.services.stream_deck_action_executor import (
    StreamDeckActionExecutor,
)
from proxdeck.infrastructure.system.desktop_launch_executor import DesktopLaunchExecutor
from proxdeck.infrastructure.system.windows_media_session_reader import WindowsMediaSessionReader
from proxdeck.presentation.widgets.clock_widget_host import build_clock_widget_host
from proxdeck.presentation.widgets.launcher_widget_host import build_launcher_widget_host
from proxdeck.presentation.widgets.media_controls_widget_host import (
    build_media_controls_widget_host,
)
from proxdeck.presentation.widgets.notes_widget_host import build_notes_widget_host
from proxdeck.presentation.widgets.stream_deck_widget_host import (
    build_stream_deck_widget_host,
)
from proxdeck.presentation.widgets.system_stats_widget_host import (
    WindowsSystemStatsProvider,
    build_system_stats_widget_host,
)
from proxdeck.presentation.widgets.web_widget_host import build_web_widget_host

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    Qt = None
    QFrame = object
    QLabel = object
    QVBoxLayout = object
    QWidget = object


class WidgetHostFactory:
    def __init__(
        self,
        media_session_reader: WindowsMediaSessionReader | None = None,
        system_stats_provider: WindowsSystemStatsProvider | None = None,
        stream_deck_action_executor: StreamDeckActionExecutor | None = None,
    ) -> None:
        self._media_session_reader = media_session_reader or WindowsMediaSessionReader()
        self._system_stats_provider = system_stats_provider or WindowsSystemStatsProvider()
        self._stream_deck_action_executor = stream_deck_action_executor or StreamDeckActionExecutor(
            DesktopLaunchExecutor()
        )
        self._builders: dict[str, Callable[[WidgetInstance, WidgetDefinition | None], QWidget]] = {
            "clock": self._build_clock_widget,
            "community-browser": self._build_community_browser_widget,
            "launcher": self._build_launcher_widget,
            "stream-deck": self._build_stream_deck_widget,
            "notes": self._build_notes_widget,
            "system-stats": self._build_system_stats_widget,
            "web": self._build_web_widget,
            "media-controls": self._build_media_controls_widget,
        }

    def create_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None = None,
        on_widget_settings_changed: Callable[[str, dict[str, object]], None] | None = None,
        live_updates: bool = True,
    ) -> QWidget:
        if Qt is None:
            raise RuntimeError("PySide6 is required to build runtime widgets")

        if widget_instance.widget_id == "notes":
            return self._build_notes_widget(
                widget_instance,
                widget_definition,
                on_widget_settings_changed=on_widget_settings_changed,
            )

        builder = self._builders.get(widget_instance.widget_id, self._build_unknown_widget)
        if widget_instance.widget_id == "clock":
            return self._build_clock_widget(widget_instance, widget_definition, live_updates=live_updates)
        if widget_instance.widget_id == "system-stats":
            return self._build_system_stats_widget(widget_instance, widget_definition, live_updates=live_updates)
        if widget_instance.widget_id == "media-controls":
            return self._build_media_controls_widget(widget_instance, widget_definition, live_updates=live_updates)
        return builder(widget_instance, widget_definition)

    def _build_card(
        self,
        detail: str,
    ) -> QWidget:
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        card.setStyleSheet(
            "QFrame {"
            "background: #101822;"
            "border: none;"
            "border-radius: 0px;"
            "padding: 12px;"
            "}"
            "QLabel { color: #E7EEF7; }"
        )
        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        detail_label = QLabel(detail)
        detail_label.setWordWrap(True)
        detail_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(detail_label)
        layout.addStretch(1)
        return card

    def _build_clock_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
        live_updates: bool = True,
    ) -> QWidget:
        return build_clock_widget_host(
            widget_instance=widget_instance,
            widget_definition=widget_definition,
            footer=self._build_metadata_footer(widget_definition),
            live_updates=live_updates,
        )

    def _build_launcher_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
    ) -> QWidget:
        return build_launcher_widget_host(
            widget_instance=widget_instance,
            widget_definition=widget_definition,
            footer=self._build_metadata_footer(widget_definition),
        )

    def _build_community_browser_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
    ) -> QWidget:
        return self._build_card(
            detail="Sample installable widget placeholder discovered from installable_widgets/.",
        )

    def _build_notes_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
        on_widget_settings_changed: Callable[[str, dict[str, object]], None] | None = None,
    ) -> QWidget:
        return build_notes_widget_host(
            widget_instance=widget_instance,
            widget_definition=widget_definition,
            footer=self._build_metadata_footer(widget_definition),
            on_settings_changed=on_widget_settings_changed,
        )

    def _build_stream_deck_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
    ) -> QWidget:
        return build_stream_deck_widget_host(
            widget_instance=widget_instance,
            widget_definition=widget_definition,
            footer=self._build_metadata_footer(widget_definition),
            action_executor=self._stream_deck_action_executor,
        )

    def _build_system_stats_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
        live_updates: bool = True,
    ) -> QWidget:
        return build_system_stats_widget_host(
            widget_instance=widget_instance,
            widget_definition=widget_definition,
            footer=self._build_metadata_footer(widget_definition),
            provider=self._system_stats_provider,
            live_updates=live_updates,
        )

    def _build_web_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
    ) -> QWidget:
        return build_web_widget_host(
            widget_instance=widget_instance,
            widget_definition=widget_definition,
            footer=self._build_metadata_footer(widget_definition),
        )

    def _build_media_controls_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
        live_updates: bool = True,
    ) -> QWidget:
        return build_media_controls_widget_host(
            widget_instance=widget_instance,
            widget_definition=widget_definition,
            footer=self._build_metadata_footer(widget_definition),
            session_reader=self._media_session_reader,
            live_updates=live_updates,
        )

    def _build_unknown_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
    ) -> QWidget:
        return self._build_card(
            detail=f"No runtime presenter is registered for {widget_instance.widget_id}.",
        )

    def _build_metadata_footer(self, widget_definition: WidgetDefinition | None) -> str:
        if widget_definition is None:
            return "Manifest metadata unavailable."

        capabilities = ", ".join(sorted(widget_definition.capabilities.values)) or "none"
        return (
            f"Kind: {widget_definition.kind.value} | "
            f"Min app: {widget_definition.compatibility.minimum_app_version} | "
            f"Distribution: {widget_definition.install_metadata.distribution} | "
            f"Scope: {widget_definition.install_metadata.installation_scope} | "
            f"Capabilities: {capabilities}"
        )
