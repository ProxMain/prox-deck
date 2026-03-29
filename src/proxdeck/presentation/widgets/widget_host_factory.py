from __future__ import annotations

from typing import Callable

from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance

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
    def __init__(self) -> None:
        self._builders: dict[str, Callable[[WidgetInstance, WidgetDefinition | None], QWidget]] = {
            "clock": self._build_clock_widget,
            "community-browser": self._build_community_browser_widget,
            "launcher": self._build_launcher_widget,
            "notes": self._build_notes_widget,
            "system-stats": self._build_system_stats_widget,
            "web": self._build_web_widget,
            "media-controls": self._build_media_controls_widget,
        }

    def create_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None = None,
    ) -> QWidget:
        if Qt is None:
            raise RuntimeError("PySide6 is required to build runtime widgets")

        builder = self._builders.get(widget_instance.widget_id, self._build_unknown_widget)
        return builder(widget_instance, widget_definition)

    def _build_card(
        self,
        title: str,
        subtitle: str,
        detail: str,
        accent: str,
        footer: str,
    ) -> QWidget:
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        card.setStyleSheet(
            "QFrame {"
            "background: #101822;"
            f"border: 2px solid {accent};"
            "border-radius: 14px;"
            "padding: 12px;"
            "}"
            "QLabel { color: #E7EEF7; }"
        )
        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(title_label)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("font-size: 13px; color: #9DB1C7;")
        layout.addWidget(subtitle_label)

        detail_label = QLabel(detail)
        detail_label.setWordWrap(True)
        detail_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(detail_label)

        footer_label = QLabel(footer)
        footer_label.setWordWrap(True)
        footer_label.setStyleSheet("font-size: 11px; color: #89A0B8;")
        layout.addWidget(footer_label)
        layout.addStretch(1)
        return card

    def _build_clock_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
    ) -> QWidget:
        return self._build_card(
            title="Clock",
            subtitle=widget_instance.instance_id,
            detail="Builtin runtime placeholder for the clock widget.",
            accent="#48B2FF",
            footer=self._build_metadata_footer(widget_definition),
        )

    def _build_launcher_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
    ) -> QWidget:
        return self._build_card(
            title="Launcher",
            subtitle=widget_instance.instance_id,
            detail="Reserved for quick app and action launching.",
            accent="#66D18F",
            footer=self._build_metadata_footer(widget_definition),
        )

    def _build_community_browser_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
    ) -> QWidget:
        return self._build_card(
            title="Community Browser",
            subtitle=widget_instance.instance_id,
            detail="Sample installable widget placeholder discovered from installable_widgets/.",
            accent="#4ED0C3",
            footer=self._build_metadata_footer(widget_definition),
        )

    def _build_notes_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
    ) -> QWidget:
        note_preview = str(widget_instance.settings.get("note_preview", "No note content yet."))
        return self._build_card(
            title="Notes",
            subtitle=widget_instance.instance_id,
            detail=note_preview,
            accent="#F2B750",
            footer=self._build_metadata_footer(widget_definition),
        )

    def _build_system_stats_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
    ) -> QWidget:
        return self._build_card(
            title="System Stats",
            subtitle=widget_instance.instance_id,
            detail="CPU, GPU, memory, and thermals will surface here in a later slice.",
            accent="#F07A9B",
            footer=self._build_metadata_footer(widget_definition),
        )

    def _build_web_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
    ) -> QWidget:
        url = str(widget_instance.settings.get("url", "https://example.com"))
        mobile = bool(widget_instance.settings.get("force_mobile", False))
        return self._build_card(
            title="Web Widget",
            subtitle="Mobile view enabled" if mobile else "Desktop view enabled",
            detail=url,
            accent="#B58CFF",
            footer=self._build_metadata_footer(widget_definition),
        )

    def _build_media_controls_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
    ) -> QWidget:
        return self._build_card(
            title="Media Controls",
            subtitle=widget_instance.instance_id,
            detail="Playback transport and session info will land here later.",
            accent="#FF8E5E",
            footer=self._build_metadata_footer(widget_definition),
        )

    def _build_unknown_widget(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
    ) -> QWidget:
        return self._build_card(
            title="Unknown Widget",
            subtitle=widget_instance.widget_id,
            detail=f"No runtime presenter is registered for {widget_instance.widget_id}.",
            accent="#7B8794",
            footer=self._build_metadata_footer(widget_definition),
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
