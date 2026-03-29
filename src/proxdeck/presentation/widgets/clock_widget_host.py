from __future__ import annotations

from datetime import datetime

from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance

try:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QTimer = object
    QFrame = object
    QLabel = object
    QVBoxLayout = object
    QWidget = object


def format_clock_timestamp(moment: datetime) -> tuple[str, str]:
    return moment.strftime("%H:%M"), moment.strftime("%A, %d %B")


def build_clock_widget_host(
    widget_instance: WidgetInstance,
    widget_definition: WidgetDefinition | None,
    footer: str,
) -> QWidget:
    card = QFrame()
    card.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
    card.setStyleSheet(
        "QFrame {"
        "background: #0E1821;"
        "border: 2px solid #48B2FF;"
        "border-radius: 14px;"
        "padding: 12px;"
        "}"
        "QLabel { color: #E7EEF7; }"
    )
    layout = QVBoxLayout(card)
    layout.setSpacing(8)

    title_label = QLabel("Clock")
    title_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #D9F2FF;")
    layout.addWidget(title_label)

    subtitle_label = QLabel(widget_instance.instance_id)
    subtitle_label.setStyleSheet("font-size: 12px; color: #9DB1C7;")
    layout.addWidget(subtitle_label)

    time_label = QLabel()
    time_label.setStyleSheet("font-size: 44px; font-weight: 800; color: #F4FBFF;")
    layout.addWidget(time_label)

    date_label = QLabel()
    date_label.setStyleSheet("font-size: 16px; color: #A9D9F7;")
    layout.addWidget(date_label)

    footer_label = QLabel(footer)
    footer_label.setWordWrap(True)
    footer_label.setStyleSheet("font-size: 11px; color: #89A0B8;")
    layout.addWidget(footer_label)
    layout.addStretch(1)

    def refresh_clock() -> None:
        time_text, date_text = format_clock_timestamp(datetime.now())
        time_label.setText(time_text)
        date_label.setText(date_text)

    refresh_clock()
    if QTimer is not object:
        timer = QTimer(card)
        timer.setInterval(1000)
        timer.timeout.connect(refresh_clock)
        timer.start()

    return card
