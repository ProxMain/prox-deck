from __future__ import annotations

from proxdeck.application.services.stream_deck_action_executor import StreamDeckActionExecutor
from proxdeck.application.services.stream_deck_configuration import (
    child_button_definitions,
    parse_stream_deck_settings,
    visible_stream_deck_button_count,
)
from proxdeck.domain.models.stream_deck import (
    STREAM_DECK_GROUP_ACTION,
    STREAM_DECK_LAUNCH_ACTION,
    STREAM_DECK_SIZE_VARIANT_COMPACT,
    STREAM_DECK_SIZE_VARIANT_TALL,
    StreamDeckButtonDefinition,
)
from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.presentation.widgets.stream_deck_icon_catalog import (
    resolve_stream_deck_icon_asset,
)

try:
    from PySide6.QtCore import QPointF, QRectF, QSize, Qt
    from PySide6.QtGui import (
        QColor,
        QLinearGradient,
        QPainter,
        QPainterPath,
        QPen,
        QPixmap,
    )
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QSizePolicy,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QPointF = object
    QRectF = object
    QSize = object
    Qt = object
    QColor = object
    QLinearGradient = object
    QPainter = object
    QPainterPath = object
    QPen = object
    QPixmap = object
    QSvgRenderer = object
    QFrame = object
    QGridLayout = object
    QHBoxLayout = object
    QLabel = object
    QSizePolicy = object
    QToolButton = object
    QVBoxLayout = object
    QWidget = object


def build_stream_deck_widget_host(
    widget_instance: WidgetInstance,
    widget_definition: WidgetDefinition | None,
    footer: str,
    action_executor: StreamDeckActionExecutor,
) -> QWidget:
    return StreamDeckWidgetHost(
        widget_instance=widget_instance,
        widget_definition=widget_definition,
        footer=footer,
        action_executor=action_executor,
    )


class StreamDeckWidgetHost(QFrame):
    def __init__(
        self,
        widget_instance: WidgetInstance,
        widget_definition: WidgetDefinition | None,
        footer: str,
        action_executor: StreamDeckActionExecutor,
    ) -> None:
        super().__init__()
        self._widget_definition = widget_definition
        self._footer = footer
        self._action_executor = action_executor
        self._settings = parse_stream_deck_settings(widget_instance.settings)
        self._page_stack: list[tuple[str, tuple[StreamDeckButtonDefinition, ...]]] = [
            ("Stream Deck", self._settings.buttons)
        ]
        self._page_index_stack: list[int] = [0]

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.setStyleSheet(
            "QFrame {"
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #090E14,stop:0.55 #0F141B,stop:1 #070B10);"
            "border: none;"
            "border-radius: 0px;"
            "padding: 2px;"
            "}"
            "QLabel { color: #EAF0F6; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self._header = QWidget()
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        header_layout.addStretch(1)

        self._back_button = QToolButton()
        self._back_button.setText("Back")
        self._back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_button.setStyleSheet(
            "QToolButton {"
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #161E29,stop:1 #0D1219);"
            "color: #E8EEF6;"
            "border: 1px solid rgba(118, 145, 181, 0.22);"
            "border-radius: 9px;"
            "padding: 4px 8px;"
            "font-size: 10px;"
            "font-weight: 800;"
            "}"
            "QToolButton:pressed { background: #090E14; padding-top: 6px; padding-bottom: 2px; }"
        )
        self._back_button.clicked.connect(self._go_back)
        self._back_button.hide()
        header_layout.addWidget(self._back_button, 0)
        self._header.hide()
        layout.addWidget(self._header)

        self._status_label = QLabel("")
        self._status_label.hide()
        layout.addWidget(self._status_label)

        self._grid = QGridLayout()
        self._grid.setHorizontalSpacing(1)
        self._grid.setVerticalSpacing(1)
        self._grid.setContentsMargins(0, 0, 0, 0)

        self._grid_container = QWidget()
        self._grid_container.setLayout(self._grid)
        self._grid_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._grid_container, 1)

        self._page_dots = QWidget()
        self._page_dots_layout = QHBoxLayout(self._page_dots)
        self._page_dots_layout.setContentsMargins(0, 0, 0, 0)
        self._page_dots_layout.setSpacing(1)
        self._page_dots_layout.addStretch(1)
        self._page_dots_layout.addStretch(1)
        self._page_dots.hide()
        layout.addWidget(self._page_dots)
        self._rebuild()

    def _go_back(self) -> None:
        if len(self._page_stack) > 1:
            self._page_stack.pop()
            self._page_index_stack.pop()
            self._rebuild()

    def _open_group(self, button: StreamDeckButtonDefinition) -> None:
        children = child_button_definitions(button)
        if not children:
            return
        self._page_stack.append((button.label, children))
        self._page_index_stack.append(0)
        self._rebuild()

    def _show_previous_page(self) -> None:
        if self._page_index_stack[-1] <= 0:
            return
        self._page_index_stack[-1] -= 1
        self._rebuild()

    def _show_next_page(self) -> None:
        if self._page_index_stack[-1] >= self._page_count() - 1:
            return
        self._page_index_stack[-1] += 1
        self._rebuild()

    def _rebuild(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        rows, columns = _grid_dimensions_for_variant(self._settings.size_variant)
        for row in range(rows):
            self._grid.setRowStretch(row, 1)
        for column in range(columns):
            self._grid.setColumnStretch(column, 1)
        self._clear_page_dots()

        _, buttons = self._page_stack[-1]
        self._back_button.setVisible(len(self._page_stack) > 1)
        self._header.setVisible(len(self._page_stack) > 1)

        visible_count = visible_stream_deck_button_count(self._settings.size_variant)
        page_index = self._page_index_stack[-1]
        start = page_index * visible_count
        page_buttons = buttons[start : start + visible_count]
        for index, button in enumerate(page_buttons):
            row, column = _button_position_for(index, size_variant=self._settings.size_variant)
            self._grid.addWidget(
                _build_stream_deck_button(
                    button=button,
                    index=index,
                    visible_count=visible_count,
                    size_variant=self._settings.size_variant,
                    status_label=self._status_label,
                    action_executor=self._action_executor,
                    on_open_group=self._open_group,
                    on_show_previous_page=self._show_previous_page,
                    on_show_next_page=self._show_next_page,
                ),
                row,
                column,
            )
        self._rebuild_page_dots()

    def _page_count(self) -> int:
        _, buttons = self._page_stack[-1]
        visible_count = visible_stream_deck_button_count(self._settings.size_variant)
        if visible_count <= 0:
            return 1
        return max(1, (len(buttons) + visible_count - 1) // visible_count)

    def _clear_page_dots(self) -> None:
        while self._page_dots_layout.count() > 2:
            item = self._page_dots_layout.takeAt(1)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _rebuild_page_dots(self) -> None:
        page_count = self._page_count()
        self._page_dots.setVisible(page_count > 1)
        if page_count <= 1:
            return
        active_index = self._page_index_stack[-1]
        for index in range(page_count):
            dot = QWidget()
            dot.setFixedSize(8 if index == active_index else 4, 4)
            color = "#8FB7FF" if index == active_index else "rgba(255,255,255,0.14)"
            dot.setStyleSheet(
                "background: %s; border-radius: 2px;" % color
            )
            self._page_dots_layout.insertWidget(self._page_dots_layout.count() - 1, dot)


def _build_stream_deck_button(
    button: StreamDeckButtonDefinition,
    index: int,
    visible_count: int,
    size_variant: str,
    status_label: QLabel,
    action_executor: StreamDeckActionExecutor,
    on_open_group,
    on_show_previous_page,
    on_show_next_page,
) -> QToolButton:
    icon_path = _resolve_stream_deck_icon_path(button)
    control = _CinematicDeckButton(
        label=button.label,
        icon_path=icon_path,
        variant=_button_variant(button, index=index, visible_count=visible_count),
        accent=button.action_type == STREAM_DECK_GROUP_ACTION,
        size_variant=size_variant,
        on_swipe_left=on_show_next_page,
        on_swipe_right=on_show_previous_page,
    )
    control.setEnabled(_is_button_enabled(button))
    control.setToolTip(button.label)
    control.clicked.connect(
        lambda _checked=False, item=button: _handle_button_trigger(
            button=item,
            status_label=status_label,
            action_executor=action_executor,
            on_open_group=on_open_group,
        )
    )
    return control


def _handle_button_trigger(
    button: StreamDeckButtonDefinition,
    status_label: QLabel,
    action_executor: StreamDeckActionExecutor,
    on_open_group,
) -> None:
    if button.action_type == STREAM_DECK_GROUP_ACTION:
        on_open_group(button)
        return
    result = action_executor.execute(button)
    status_label.setText(result.message)


def _is_button_enabled(button: StreamDeckButtonDefinition) -> bool:
    if button.action_type == STREAM_DECK_GROUP_ACTION:
        return bool(child_button_definitions(button))
    if button.action_type != STREAM_DECK_LAUNCH_ACTION:
        return False
    return bool(str(button.action_config.get("target", "")).strip())


def _grid_dimensions_for_variant(size_variant: str) -> tuple[int, int]:
    if size_variant == STREAM_DECK_SIZE_VARIANT_TALL:
        return (4, 8)
    return (2, 8)


def _button_position_for(index: int, *, size_variant: str) -> tuple[int, int]:
    rows, columns = _grid_dimensions_for_variant(size_variant)
    bounded_index = index % (rows * columns)
    return (bounded_index // columns, bounded_index % columns)


def _button_variant(
    button: StreamDeckButtonDefinition,
    *,
    index: int,
    visible_count: int,
) -> str:
    if index >= max(0, visible_count - 2):
        return "utility"
    if button.action_type == STREAM_DECK_GROUP_ACTION:
        return "accent"
    return "primary"


def _build_footer_text(
    widget_definition: WidgetDefinition | None,
    footer: str,
    size_variant: str,
) -> str:
    label = "Compact" if size_variant == "1/6" else "Tall"
    if widget_definition is None:
        return f"{label} deck"
    return f"{label} deck | {footer}"


def _resolve_stream_deck_icon_path(button: StreamDeckButtonDefinition) -> str | None:
    asset_path = resolve_stream_deck_icon_asset(button.icon or "")
    if asset_path is None:
        return None
    return str(asset_path)


class _CinematicDeckButton(QToolButton):
    def __init__(
        self,
        label: str,
        icon_path: str | None,
        variant: str,
        accent: bool,
        size_variant: str,
        on_swipe_left,
        on_swipe_right,
    ) -> None:
        super().__init__()
        self._label = label
        self._icon_path = icon_path
        self._variant = variant
        self._accent = accent
        self._size_variant = size_variant
        self._on_swipe_left = on_swipe_left
        self._on_swipe_right = on_swipe_right
        self._press_pos = None
        self._swipe_consumed = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(False)
        self.setAutoRaise(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preferred_width, preferred_height = self._preferred_size()
        self.setMinimumSize(preferred_width, preferred_height)
        self.setText("")
        self.setStyleSheet("QToolButton { background: transparent; border: none; }")

    def sizeHint(self):  # type: ignore[override]
        width, height = self._preferred_size()
        return QSize(width, height)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        outer_rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        side = min(outer_rect.width(), outer_rect.height())
        tile_rect = QRectF(
            outer_rect.center().x() - side / 2,
            outer_rect.center().y() - side / 2,
            side,
            side,
        )

        painter.save()
        painter.translate(0, 0.8 if self.isDown() else 0)
        self._paint_shadow(painter, tile_rect)
        self._paint_tile(painter, tile_rect)
        self._paint_icon(painter, tile_rect)
        self._paint_badges(painter, tile_rect)
        painter.restore()

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self._press_pos = event.position()
        self._swipe_consumed = False
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        if self._press_pos is not None:
            delta = event.position() - self._press_pos
            if abs(delta.x()) > 32 and abs(delta.x()) > abs(delta.y()):
                self._swipe_consumed = True
                if delta.x() < 0:
                    self._on_swipe_left()
                else:
                    self._on_swipe_right()
                event.accept()
                self.update()
                return
        super().mouseReleaseEvent(event)

    def _paint_shadow(self, painter: QPainter, rect: QRectF) -> None:
        shadow_rect = rect.adjusted(0.2, 0.8, -0.2, 1.0)
        shadow_path = QPainterPath()
        shadow_radius = self._corner_radius(shadow_rect)
        shadow_path.addRoundedRect(shadow_rect, shadow_radius, shadow_radius)
        shadow_gradient = QLinearGradient(shadow_rect.topLeft(), shadow_rect.bottomRight())
        shadow_gradient.setColorAt(0.0, QColor(7, 10, 14, 0))
        shadow_gradient.setColorAt(0.25, QColor(7, 10, 14, 40))
        shadow_gradient.setColorAt(1.0, QColor(2, 4, 7, 110))
        painter.fillPath(shadow_path, shadow_gradient)

    def _paint_tile(self, painter: QPainter, rect: QRectF) -> None:
        radius = self._corner_radius(rect)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        painter.fillPath(path, self._base_gradient(rect))

        glow_path = QPainterPath()
        glow_path.addRoundedRect(rect.adjusted(1, 1, -1, -1), radius - 1, radius - 1)
        painter.fillPath(glow_path, self._ambient_gradient(rect))

        inner_rect = rect.adjusted(1.6, 1.6, -1.6, -1.6)
        inner_path = QPainterPath()
        inner_radius = max(4.0, radius - 6)
        inner_path.addRoundedRect(inner_rect, inner_radius, inner_radius)
        painter.fillPath(inner_path, self._inner_surface_gradient(inner_rect))

        highlight_pen = QPen(self._highlight_color(), 0.9)
        painter.setPen(highlight_pen)
        painter.drawRoundedRect(rect.adjusted(0.6, 0.6, -0.6, -0.6), radius, radius)

        seam_pen = QPen(QColor(255, 255, 255, 18), 1.0)
        painter.setPen(seam_pen)
        painter.drawLine(
            QPointF(inner_rect.left() + 4, inner_rect.top() + 3.5),
            QPointF(inner_rect.right() - 4, inner_rect.top() + 3.5),
        )

        if self.isDown():
            inset_path = QPainterPath()
            inset_path.addRoundedRect(
                inner_rect.adjusted(1, 1, -1, -1),
                max(3.0, radius - 8),
                max(3.0, radius - 8),
            )
            inset = QLinearGradient(inner_rect.topLeft(), inner_rect.bottomLeft())
            inset.setColorAt(0.0, QColor(0, 0, 0, 110))
            inset.setColorAt(0.3, QColor(0, 0, 0, 45))
            inset.setColorAt(1.0, QColor(255, 255, 255, 10))
            painter.fillPath(inset_path, inset)

    def _paint_icon(self, painter: QPainter, rect: QRectF) -> None:
        if not self._icon_path:
            return
        safe_rect = rect.adjusted(2.5, 2.5, -2.5, -2.5)
        clip_path = QPainterPath()
        clip_path.addRoundedRect(safe_rect, max(5.0, self._corner_radius(safe_rect) - 3), max(5.0, self._corner_radius(safe_rect) - 3))
        painter.save()
        painter.setClipPath(clip_path)
        icon_size = int(min(safe_rect.width(), safe_rect.height()) * 1.24)
        icon_rect = QRectF(
            safe_rect.center().x() - icon_size / 2,
            safe_rect.center().y() - icon_size / 2 + 0.5,
            icon_size,
            icon_size,
        )
        if self._icon_path.lower().endswith(".svg") and QSvgRenderer is not object:
            renderer = QSvgRenderer(self._icon_path)
            if renderer.isValid():
                renderer.render(painter, icon_rect)
                painter.restore()
                return
        if QPixmap is object:
            painter.restore()
            return
        pixmap = QPixmap(self._icon_path)
        if pixmap.isNull():
            painter.restore()
            return
        painter.drawPixmap(icon_rect.toRect(), pixmap)
        painter.restore()

    def _paint_badges(self, painter: QPainter, rect: QRectF) -> None:
        top_badge = QRectF(rect.left() + 4, rect.top() + 3.0, rect.width() - 8, 2.2)
        badge = QLinearGradient(top_badge.topLeft(), top_badge.topRight())
        badge.setColorAt(0.0, QColor(255, 255, 255, 62 if self.isEnabled() else 20))
        badge.setColorAt(0.6, QColor(255, 255, 255, 18))
        badge.setColorAt(1.0, QColor(255, 255, 255, 0))
        badge_path = QPainterPath()
        badge_path.addRoundedRect(top_badge, 2, 2)
        painter.fillPath(badge_path, badge)

        dot_rect = QRectF(rect.right() - 7.2, rect.top() + 4.2, 2.8, 2.8)
        dot_color = QColor(134, 168, 255, 210) if self._accent else QColor(233, 242, 250, 120)
        if not self.isEnabled():
            dot_color = QColor(110, 120, 132, 90)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(dot_color)
        painter.drawEllipse(dot_rect)

    def _base_gradient(self, rect: QRectF) -> QLinearGradient:
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        if self._variant == "utility":
            gradient.setColorAt(0.0, QColor(246, 249, 253))
            gradient.setColorAt(0.18, QColor(230, 236, 243))
            gradient.setColorAt(0.58, QColor(194, 204, 216))
            gradient.setColorAt(1.0, QColor(161, 174, 189))
            return gradient
        if self._accent:
            gradient.setColorAt(0.0, QColor(48, 73, 109))
            gradient.setColorAt(0.18, QColor(31, 50, 75))
            gradient.setColorAt(0.58, QColor(18, 27, 39))
            gradient.setColorAt(1.0, QColor(11, 15, 22))
            return gradient
        gradient.setColorAt(0.0, QColor(49, 60, 75))
        gradient.setColorAt(0.12, QColor(34, 43, 56))
        gradient.setColorAt(0.52, QColor(20, 26, 35))
        gradient.setColorAt(1.0, QColor(10, 14, 20))
        return gradient

    def _ambient_gradient(self, rect: QRectF) -> QLinearGradient:
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        top_alpha = 40 if self.underMouse() and self.isEnabled() else 24
        accent_alpha = 46 if self._accent and self.isEnabled() else 18
        if not self.isEnabled():
            top_alpha = 12
            accent_alpha = 10
        gradient.setColorAt(0.0, QColor(255, 255, 255, top_alpha))
        gradient.setColorAt(0.16, QColor(99, 153, 255, accent_alpha))
        gradient.setColorAt(0.75, QColor(14, 20, 28, 0))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
        return gradient

    def _inner_surface_gradient(self, rect: QRectF) -> QLinearGradient:
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        if self._variant == "utility":
            gradient.setColorAt(0.0, QColor(255, 255, 255, 82))
            gradient.setColorAt(0.20, QColor(255, 255, 255, 28))
            gradient.setColorAt(1.0, QColor(130, 143, 158, 14))
            return gradient
        gradient.setColorAt(0.0, QColor(255, 255, 255, 28))
        gradient.setColorAt(0.16, QColor(255, 255, 255, 10))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 20))
        return gradient

    def _highlight_color(self) -> QColor:
        if not self.isEnabled():
            return QColor(116, 126, 137, 28)
        if self._variant == "utility":
            return QColor(255, 255, 255, 88)
        if self._accent:
            return QColor(129, 164, 255, 110)
        return QColor(176, 198, 222, 70)

    def _preferred_size(self) -> tuple[int, int]:
        if self._size_variant == STREAM_DECK_SIZE_VARIANT_TALL:
            return (30, 30)
        return (42, 42)

    def _corner_radius(self, rect: QRectF) -> float:
        return max(6.0, min(rect.width(), rect.height()) * 0.22)
