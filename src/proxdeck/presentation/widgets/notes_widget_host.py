from __future__ import annotations

from collections.abc import Callable

from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance

try:
    from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QFrame = object
    QLabel = object
    QPushButton = object
    QTextEdit = object
    QVBoxLayout = object
    QWidget = object


def build_notes_widget_host(
    widget_instance: WidgetInstance,
    widget_definition: WidgetDefinition | None,
    footer: str,
    on_settings_changed: Callable[[str, dict[str, object]], None] | None = None,
) -> QWidget:
    card = QFrame()
    card.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
    card.setStyleSheet(
        "QFrame {"
        "background: #19140A;"
        "border: none;"
        "border-radius: 14px;"
        "padding: 12px;"
        "}"
        "QLabel { color: #FFF8E7; }"
        "QTextEdit {"
        "background: #2A210F;"
        "color: #FFF8E7;"
        "border: 1px solid #7D6530;"
        "border-radius: 10px;"
        "padding: 8px;"
        "}"
        "QPushButton {"
        "background: #F2B750;"
        "color: #261C08;"
        "border: none;"
        "border-radius: 10px;"
        "padding: 8px 12px;"
        "font-weight: 700;"
        "}"
    )
    layout = QVBoxLayout(card)
    layout.setSpacing(8)

    editor = QTextEdit()
    editor.setPlaceholderText("Type a note for this screen...")
    editor.setPlainText(str(widget_instance.settings.get("content", "")))
    layout.addWidget(editor, 1)

    save_button = QPushButton("Save Note")
    layout.addWidget(save_button)

    def save_note() -> None:
        if on_settings_changed is None:
            return
        content = editor.toPlainText().strip()
        on_settings_changed(
            widget_instance.instance_id,
            {
                **widget_instance.settings,
                "content": content,
                "note_preview": content[:140],
            },
        )

    save_button.clicked.connect(save_note)
    return card
