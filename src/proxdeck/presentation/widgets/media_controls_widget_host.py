from __future__ import annotations

import ctypes
import math
from dataclasses import dataclass

from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.infrastructure.system.windows_media_session_reader import (
    MediaSessionSnapshot,
    WindowsMediaSessionReader,
    unavailable_media_session,
)

try:
    from PySide6.QtCore import QRectF, QSize, QTimer, Qt
    from PySide6.QtGui import QColor, QPainter, QPainterPath
    from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QRectF = object
    QSize = object
    QTimer = object
    Qt = object
    QColor = object
    QPainter = object
    QPainterPath = object
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
    session_reader: WindowsMediaSessionReader,
    live_updates: bool = True,
) -> QWidget:
    card = QWidget()
    card.setToolTip(footer)
    card.setStyleSheet(
        "QWidget {"
        "background: qradialgradient(cx:0.22, cy:0.18, radius:1.05, fx:0.22, fy:0.18, "
        "stop:0 #3A2418, stop:0.3 #24160F, stop:0.72 #140D09, stop:1 #090605);"
        "border: none;"
        "border-radius: 0px;"
        "}"
        "QLabel { background: transparent; border: none; }"
    )

    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    stage = _MediaControlStrip()
    stage.setMinimumHeight(160)
    layout.addWidget(stage, 1)

    status_label = QLabel("Start playback in Spotify, YouTube, VLC, or another media app.")
    status_label.setWordWrap(True)
    status_label.setStyleSheet(
        "font-size: 12px; font-weight: 700; color: rgba(224, 178, 145, 0.88);"
    )
    layout.addWidget(status_label, 0, Qt.AlignmentFlag.AlignHCenter)

    def refresh_media_state() -> None:
        snapshot = session_reader.read_current_session()
        stage.set_session_snapshot(snapshot)
        status_label.setText(_status_text_for(snapshot))

    refresh_media_state()
    if live_updates and QTimer is not object:
        card._media_refresh_timer = QTimer(card)  # type: ignore[attr-defined]
        card._media_refresh_timer.setInterval(33)  # type: ignore[attr-defined]
        card._media_refresh_timer.timeout.connect(refresh_media_state)  # type: ignore[attr-defined]
        card._media_refresh_timer.start()  # type: ignore[attr-defined]

    stage.bind_status_label(status_label)
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
        status_label.setText(f"Sent {action.label} to the active Windows media session.")
    else:
        status_label.setText(f"Unable to send {action.label} in this environment.")


class _MediaControlStrip(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._status_label: QLabel | None = None
        self._buttons: dict[str, _TransportIconButton] = {}
        self._session = unavailable_media_session()
        self._animation_phase = 0.0
        self._build_buttons()
        if QTimer is not object:
            self._animation_timer = QTimer(self)
            self._animation_timer.setInterval(33)
            self._animation_timer.timeout.connect(self._advance_animation)
            self._animation_timer.start()

    def bind_status_label(self, status_label: QLabel) -> None:
        self._status_label = status_label

    def set_session_snapshot(self, snapshot: MediaSessionSnapshot) -> None:
        self._session = snapshot
        play_button = self._buttons.get("Play/Pause")
        if play_button is not None:
            play_button.set_playing(snapshot.is_playing)
        self.update()

    def _build_buttons(self) -> None:
        for action in media_actions():
            button = _TransportIconButton(action.label)
            button.setParent(self)
            button.clicked.connect(
                lambda _checked=False, selected_action=action: self._handle_action(selected_action)
            )
            self._buttons[action.label] = button

    def _handle_action(self, action: MediaAction) -> None:
        if self._status_label is None:
            return
        _trigger_media_action(action, self._status_label)

    def _advance_animation(self) -> None:
        self._animation_phase = (self._animation_phase + 0.42) % (math.pi * 8)
        self.update()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        width = self.width()
        center_x = width // 2
        line_y = 76
        button_y = 98

        play_size = 48
        side_size = 40
        offset_x = 58

        self._set_button_geometry("Play/Pause", center_x - play_size // 2, button_y, play_size)
        self._set_button_geometry("Previous", center_x - offset_x - side_size // 2, button_y + 4, side_size)
        self._set_button_geometry("Next", center_x + offset_x - side_size // 2, button_y + 4, side_size)
        self._line_rect = QRectF(18, line_y, max(40, width - 36), 4)
        self._spectrum_rect = QRectF(18, 10, max(40, width - 36), 52)

    def _set_button_geometry(self, action_label: str, x: int, y: int, size: int) -> None:
        self._buttons[action_label].setGeometry(x, y, size, size)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        if QPainter is object:
            return super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        spectrum_rect = getattr(self, "_spectrum_rect", QRectF(18, 10, max(40, self.width() - 36), 52))
        self._draw_spectrum(painter, spectrum_rect)

        line_rect = getattr(self, "_line_rect", QRectF(18, 34, max(40, self.width() - 36), 4))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(104, 69, 49, 150))
        painter.drawRoundedRect(line_rect, 2, 2)

        progress = _timeline_progress(self._session)
        if progress > 0:
            fill_rect = QRectF(line_rect)
            fill_rect.setWidth(max(6.0, line_rect.width() * progress))
            painter.setBrush(QColor(247, 187, 108, 235))
            painter.drawRoundedRect(fill_rect, 2, 2)

    def _draw_spectrum(self, painter: QPainter, rect: QRectF) -> None:
        bar_count = 22
        gap = 4.0
        bar_width = max(3.0, (rect.width() - gap * (bar_count - 1)) / bar_count)
        baseline = rect.bottom()
        active = self._session.is_playing is True or (self._session.audio_level or 0.0) > 0.01
        track_seed = (sum(ord(char) for char in self._session.title) % 11) / 11.0 if self._session.title else 0.0
        progress = _timeline_progress(self._session)
        energy = min(1.0, max(0.0, (self._session.audio_level or 0.0) * 1.9))

        for index in range(bar_count):
            x = rect.left() + index * (bar_width + gap)
            wave = math.sin(self._animation_phase + index * 0.55 + progress * math.pi * 4)
            ripple = math.sin((self._animation_phase * 0.6) + index * 1.1 + track_seed * math.pi * 2)
            normalized = 0.12 + energy * 0.18 + (wave + 1.0) * (0.12 + energy * 0.14) + (ripple + 1.0) * (0.06 + energy * 0.08)
            if not active:
                idle_wave = math.sin((self._animation_phase * 0.75) + index * 0.45)
                idle_ripple = math.sin((self._animation_phase * 0.33) + index * 0.9)
                normalized = 0.14 + (idle_wave + 1.0) * 0.09 + (idle_ripple + 1.0) * 0.05
            bar_height = rect.height() * max(0.12, min(0.92, normalized))
            top = baseline - bar_height

            alpha = 220 if active else 150
            color = QColor(255, 201, 128, alpha)
            if index % 3 == 0:
                color = QColor(255, 228, 178, alpha)

            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(x, top, bar_width, bar_height), 1.8, 1.8)

    def minimumSizeHint(self):  # type: ignore[override]
        if QSize is object:
            return super().minimumSizeHint()
        return self.sizeHint()

    def sizeHint(self):  # type: ignore[override]
        if QSize is object:
            return super().sizeHint()
        return QSize(280, 160)


class _TransportIconButton(QPushButton):
    def __init__(self, action_label: str) -> None:
        super().__init__("")
        self._action_label = action_label
        self._is_playing: bool | None = None
        self._apply_style()

    def set_playing(self, is_playing: bool | None) -> None:
        self._is_playing = is_playing
        self.update()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            "QPushButton {"
            "background: transparent;"
            "border: none;"
            "padding: 0px;"
            "}"
        )

    def paintEvent(self, event) -> None:  # type: ignore[override]
        super().paintEvent(event)
        if QPainter is object or QPainterPath is object:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#FFF1E4"))

        icon_rect = QRectF(self.rect()).adjusted(
            self.width() * 0.2,
            self.height() * 0.2,
            -self.width() * 0.2,
            -self.height() * 0.2,
        )
        if self._action_label == "Play/Pause":
            self._draw_play_pause_icon(painter, icon_rect)
        elif self._action_label == "Previous":
            self._draw_skip_icon(painter, icon_rect, reverse=True)
        else:
            self._draw_skip_icon(painter, icon_rect, reverse=False)

    def _draw_play_pause_icon(self, painter: QPainter, rect: QRectF) -> None:
        if self._is_playing:
            bar_width = rect.width() * 0.18
            gap = rect.width() * 0.16
            left_x = rect.center().x() - gap / 2 - bar_width
            right_x = rect.center().x() + gap / 2
            painter.drawRoundedRect(QRectF(left_x, rect.top(), bar_width, rect.height()), 2, 2)
            painter.drawRoundedRect(QRectF(right_x, rect.top(), bar_width, rect.height()), 2, 2)
            return

        path = QPainterPath()
        path.moveTo(rect.left(), rect.top())
        path.lineTo(rect.right(), rect.center().y())
        path.lineTo(rect.left(), rect.bottom())
        path.closeSubpath()
        painter.drawPath(path)

    def _draw_skip_icon(self, painter: QPainter, rect: QRectF, reverse: bool) -> None:
        bar_width = rect.width() * 0.1
        triangle_width = (rect.width() - bar_width - rect.width() * 0.08) / 2
        gap = rect.width() * 0.08
        if reverse:
            bar_rect = QRectF(rect.left(), rect.top(), bar_width, rect.height())
            first = QRectF(bar_rect.right() + gap, rect.top(), triangle_width, rect.height())
            second = QRectF(first.right(), rect.top(), triangle_width, rect.height())
        else:
            bar_rect = QRectF(rect.right() - bar_width, rect.top(), bar_width, rect.height())
            second = QRectF(rect.left(), rect.top(), triangle_width, rect.height())
            first = QRectF(second.right(), rect.top(), triangle_width, rect.height())

        painter.drawRoundedRect(bar_rect, 1.5, 1.5)
        self._draw_triangle(painter, first, reverse=reverse)
        self._draw_triangle(painter, second, reverse=reverse)

    def _draw_triangle(self, painter: QPainter, rect: QRectF, reverse: bool) -> None:
        path = QPainterPath()
        if reverse:
            path.moveTo(rect.right(), rect.top())
            path.lineTo(rect.left(), rect.center().y())
            path.lineTo(rect.right(), rect.bottom())
        else:
            path.moveTo(rect.left(), rect.top())
            path.lineTo(rect.right(), rect.center().y())
            path.lineTo(rect.left(), rect.bottom())
        path.closeSubpath()
        painter.drawPath(path)


def _status_text_for(snapshot: MediaSessionSnapshot) -> str:
    if not snapshot.is_available:
        return "Start playback in Spotify, YouTube, VLC, or another media app."
    if snapshot.artist == "Active audio session":
        return f"{snapshot.source_app}  |  Active audio session"
    return f"{snapshot.title}  |  {snapshot.artist}"


def _timeline_progress(snapshot: MediaSessionSnapshot) -> float:
    if snapshot.position_seconds is None or snapshot.duration_seconds is None or snapshot.duration_seconds <= 0:
        return 0.0
    return max(0.0, min(1.0, snapshot.position_seconds / snapshot.duration_seconds))
