from __future__ import annotations

import ctypes
from dataclasses import dataclass

from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance

try:
    from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QFrame = object
    QGridLayout = object
    QLabel = object
    QPushButton = object
    QVBoxLayout = object
    QWidget = object


VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1


@dataclass(frozen=True)
class MediaAction:
    label: str
    virtual_key: int


def media_actions() -> tuple[MediaAction, ...]:
    return (
        MediaAction(label="Previous", virtual_key=VK_MEDIA_PREV_TRACK),
        MediaAction(label="Play/Pause", virtual_key=VK_MEDIA_PLAY_PAUSE),
        MediaAction(label="Next", virtual_key=VK_MEDIA_NEXT_TRACK),
    )


def build_media_controls_widget_host(
    widget_instance: WidgetInstance,
    widget_definition: WidgetDefinition | None,
    footer: str,
) -> QWidget:
    card = QFrame()
    card.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
    card.setStyleSheet(
        "QFrame {"
        "background: #1A120E;"
        "border: 2px solid #FF8E5E;"
        "border-radius: 14px;"
        "padding: 12px;"
        "}"
        "QLabel { color: #FFF1E8; }"
        "QPushButton {"
        "background: #4A2A1D;"
        "color: #FFF1E8;"
        "border: 1px solid #A35636;"
        "border-radius: 12px;"
        "padding: 12px;"
        "font-size: 14px;"
        "font-weight: 700;"
        "}"
        "QPushButton:hover { background: #5C3424; }"
    )
    layout = QVBoxLayout(card)
    layout.setSpacing(8)

    title_label = QLabel("Media Controls")
    title_label.setStyleSheet("font-size: 20px; font-weight: 700;")
    layout.addWidget(title_label)

    subtitle_label = QLabel(widget_instance.instance_id)
    subtitle_label.setStyleSheet("font-size: 13px; color: #F3B59C;")
    layout.addWidget(subtitle_label)

    status_label = QLabel("Send transport commands to the active system media session.")
    status_label.setWordWrap(True)
    status_label.setStyleSheet("font-size: 12px; color: #E5B7A2;")
    layout.addWidget(status_label)

    grid = QGridLayout()
    grid.setSpacing(8)
    for index, action in enumerate(media_actions()):
        button = QPushButton(action.label)
        button.clicked.connect(
            lambda _checked=False, selected_action=action: _trigger_media_action(
                selected_action,
                status_label,
            )
        )
        grid.addWidget(button, 0, index)
    layout.addLayout(grid)

    footer_label = QLabel(footer)
    footer_label.setWordWrap(True)
    footer_label.setStyleSheet("font-size: 11px; color: #CFA089;")
    layout.addWidget(footer_label)
    layout.addStretch(1)
    return card


def send_media_key(virtual_key: int) -> bool:
    if not hasattr(ctypes, "windll"):
        return False
    user32 = ctypes.windll.user32
    user32.keybd_event(virtual_key, 0, 0, 0)
    user32.keybd_event(virtual_key, 0, 0x0002, 0)
    return True


def _trigger_media_action(action: MediaAction, status_label: QLabel) -> None:
    success = send_media_key(action.virtual_key)
    if success:
        status_label.setText(f"Sent {action.label} command.")
    else:
        status_label.setText(f"Unable to send {action.label} command in this environment.")
