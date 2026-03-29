from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance

DAY_NAMES_NL = (
    "Maandag",
    "Dinsdag",
    "Woensdag",
    "Donderdag",
    "Vrijdag",
    "Zaterdag",
    "Zondag",
)

MONTH_NAMES_NL = (
    "Januari",
    "Februari",
    "Maart",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Augustus",
    "September",
    "Oktober",
    "November",
    "December",
)


@dataclass(frozen=True)
class ClockDisplayState:
    time_text: str
    day_name: str
    date_text: str
    hour: int
    minute: int
    second: int


try:
    from PySide6.QtCore import QTimer, Qt
    from PySide6.QtGui import QColor, QConicalGradient, QFont, QLinearGradient, QPainter, QPen, QRadialGradient
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QTimer = object
    Qt = object
    QColor = object
    QConicalGradient = object
    QFont = object
    QLinearGradient = object
    QPainter = object
    QPen = object
    QRadialGradient = object
    QFrame = object
    QHBoxLayout = object
    QLabel = object
    QVBoxLayout = object
    QWidget = object


def build_clock_display_state(moment: datetime) -> ClockDisplayState:
    return ClockDisplayState(
        time_text=moment.strftime("%H:%M"),
        day_name=DAY_NAMES_NL[moment.weekday()],
        date_text=f"{moment.day} {MONTH_NAMES_NL[moment.month - 1]} {moment.year}",
        hour=moment.hour,
        minute=moment.minute,
        second=moment.second,
    )


def format_clock_timestamp(moment: datetime) -> tuple[str, str]:
    state = build_clock_display_state(moment)
    return state.time_text, f"{state.day_name}, {state.date_text}"


def build_clock_widget_host(
    widget_instance: WidgetInstance,
    widget_definition: WidgetDefinition | None,
    footer: str,
) -> QWidget:
    card = QFrame()
    card.setStyleSheet(
        "QFrame {"
        "background: qradialgradient(cx:0.24, cy:0.18, radius:1.05, fx:0.24, fy:0.18, "
        "stop:0 #15314A, stop:0.26 #0E2134, stop:0.62 #08121C, stop:1 #050910);"
        "border: none;"
        "border-radius: 28px;"
        "}"
        "QLabel { background: transparent; border: none; }"
    )

    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(10)

    top_bar = QWidget(card)
    top_layout = QHBoxLayout(top_bar)
    top_layout.setContentsMargins(0, 0, 0, 0)
    top_layout.setSpacing(8)

    top_layout.addStretch(1)
    layout.addWidget(top_bar)

    dial = _ClockHudScene()
    dial.setMinimumHeight(220)
    layout.addWidget(dial, 1)

    day_label = QLabel()
    day_label.setStyleSheet(
        "font-size: 15px; font-weight: 900; color: rgba(228, 247, 255, 0.98);"
    )
    layout.addWidget(day_label, 0, Qt.AlignmentFlag.AlignHCenter)

    date_label = QLabel()
    date_label.setStyleSheet(
        "font-size: 12px; font-weight: 800; letter-spacing: 0.4px; color: rgba(126, 196, 229, 0.84);"
    )
    layout.addWidget(date_label, 0, Qt.AlignmentFlag.AlignHCenter)

    def refresh_clock() -> None:
        state = build_clock_display_state(datetime.now())
        dial.set_display_state(state)
        day_label.setText(state.day_name)
        date_label.setText(state.date_text)

    refresh_clock()
    if QTimer is not object:
        timer = QTimer(card)
        timer.setInterval(1000)
        timer.timeout.connect(refresh_clock)
        timer.start()

    return card


class _ClockHudScene(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._state = build_clock_display_state(datetime.now())

    def set_display_state(self, state: ClockDisplayState) -> None:
        self._state = state
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        if QPainter is object:
            return super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(8, 6, -8, -6)
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2 - 6

        ambient = QRadialGradient(center.x(), center.y(), radius)
        ambient.setColorAt(0.0, QColor(68, 193, 255, 74))
        ambient.setColorAt(0.55, QColor(24, 88, 134, 24))
        ambient.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(ambient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, int(radius), int(radius))

        painter.setBrush(QColor(6, 14, 22, 210))
        painter.setPen(QPen(QColor(76, 156, 201, 72), 2))
        painter.drawEllipse(center, int(radius - 4), int(radius - 4))

        outer_ring = QConicalGradient(center.x(), center.y(), -90)
        outer_ring.setColorAt(0.0, QColor("#87F5FF"))
        outer_ring.setColorAt(0.3, QColor("#34A8FF"))
        outer_ring.setColorAt(0.62, QColor("#6FEAFF"))
        outer_ring.setColorAt(1.0, QColor("#87F5FF"))
        painter.setPen(QPen(outer_ring, 4))
        painter.drawEllipse(center, int(radius - 14), int(radius - 14))

        painter.setPen(QPen(QColor(103, 200, 240, 42), 2))
        painter.drawEllipse(center, int(radius - 26), int(radius - 26))
        painter.drawEllipse(center, int(radius - 42), int(radius - 42))

        self._draw_segment_arcs(painter, center, radius - 18)
        self._draw_ticks(painter, center, radius - 12)
        self._draw_crosshair(painter, center, radius - 48)
        self._draw_hands(painter, center, radius - 48)
        self._draw_center_core(painter, center)
        self._draw_time_projection(painter, rect)

    def _draw_segment_arcs(self, painter: QPainter, center, radius: float) -> None:
        painter.setPen(QPen(QColor(128, 226, 255, 112), 3))
        for start, span in ((212, 34), (162, 28), (104, 26), (42, 34), (324, 20)):
            painter.drawArc(
                int(center.x() - radius),
                int(center.y() - radius),
                int(radius * 2),
                int(radius * 2),
                start * 16,
                -span * 16,
            )

        painter.setPen(QPen(QColor(67, 137, 179, 72), 1.5))
        inner_radius = radius - 24
        for start, span in ((222, 18), (144, 16), (68, 14), (6, 16), (284, 14)):
            painter.drawArc(
                int(center.x() - inner_radius),
                int(center.y() - inner_radius),
                int(inner_radius * 2),
                int(inner_radius * 2),
                start * 16,
                -span * 16,
            )

    def _draw_ticks(self, painter: QPainter, center, radius: float) -> None:
        for tick in range(60):
            angle = math.radians((tick * 6) - 90)
            outer = radius
            inner = outer - (12 if tick % 5 == 0 else 6)
            pen = QPen(
                QColor(171, 237, 255, 210) if tick % 5 == 0 else QColor(96, 154, 193, 104),
                2 if tick % 5 == 0 else 1,
            )
            painter.setPen(pen)
            outer_x, outer_y = _point(center.x(), center.y(), outer, angle)
            inner_x, inner_y = _point(center.x(), center.y(), inner, angle)
            painter.drawLine(outer_x, outer_y, inner_x, inner_y)

    def _draw_crosshair(self, painter: QPainter, center, radius: float) -> None:
        painter.setPen(QPen(QColor(95, 164, 203, 48), 1))
        painter.drawLine(int(center.x() - radius), center.y(), int(center.x() + radius), center.y())
        painter.drawLine(center.x(), int(center.y() - radius), center.x(), int(center.y() + radius))

    def _draw_hands(self, painter: QPainter, center, radius: float) -> None:
        self._draw_hand(
            painter,
            center.x(),
            center.y(),
            radius - 16,
            ((self._state.hour % 12) + self._state.minute / 60) * 30 - 90,
            QColor("#E6FBFF"),
            5,
        )
        self._draw_hand(
            painter,
            center.x(),
            center.y(),
            radius - 4,
            (self._state.minute + self._state.second / 60) * 6 - 90,
            QColor("#86F0FF"),
            3,
        )
        self._draw_hand(
            painter,
            center.x(),
            center.y(),
            radius + 6,
            self._state.second * 6 - 90,
            QColor("#38CFFF"),
            1.5,
        )

    def _draw_center_core(self, painter: QPainter, center) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#91F3FF"))
        painter.drawEllipse(center, 9, 9)
        painter.setBrush(QColor("#07121A"))
        painter.drawEllipse(center, 4, 4)

    def _draw_time_projection(self, painter: QPainter, rect) -> None:
        projection_rect = rect.adjusted(22, rect.height() - 62, -22, -10)

        value_font = painter.font()
        value_font.setPointSize(14)
        if QFont is not object:
            value_font.setWeight(QFont.Weight.ExtraBold)
        painter.setFont(value_font)
        painter.setPen(QColor(229, 248, 255))
        painter.drawText(projection_rect, Qt.AlignmentFlag.AlignCenter, self._state.time_text)

    def _draw_hand(
        self,
        painter: QPainter,
        center_x: float,
        center_y: float,
        length: float,
        angle_degrees: float,
        color: QColor,
        width: float,
    ) -> None:
        angle = math.radians(angle_degrees)
        painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        start_x, start_y = _point(center_x, center_y, length * -0.18, angle)
        end_x, end_y = _point(center_x, center_y, length, angle)
        painter.drawLine(start_x, start_y, end_x, end_y)


def _point(center_x: float, center_y: float, radius: float, angle: float):
    return int(center_x + math.cos(angle) * radius), int(center_y + math.sin(angle) * radius)
