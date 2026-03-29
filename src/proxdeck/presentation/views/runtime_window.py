from __future__ import annotations

from proxdeck.application.controllers.management_controller import ManagementController
from proxdeck.application.controllers.runtime_controller import RuntimeController
from proxdeck.application.dto.runtime_state import RuntimeState
from proxdeck.bootstrap.settings import APP_RELEASE
from proxdeck.domain.models.screen import Screen
from proxdeck.presentation.widgets.widget_host_factory import WidgetHostFactory

try:
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QColor, QConicalGradient, QFont, QLinearGradient, QPainter, QPen, QRadialGradient
    from PySide6.QtWidgets import (
        QComboBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QEvent = object
    QPointF = object
    Qt = None
    QColor = object
    QConicalGradient = object
    QFont = object
    QLinearGradient = object
    QPainter = object
    QPen = object
    QRadialGradient = object
    QComboBox = object
    QFrame = object
    QGridLayout = object
    QHBoxLayout = object
    QLabel = object
    QMainWindow = object
    QSizePolicy = object
    QVBoxLayout = object
    QWidget = object


class RuntimeWindow(QMainWindow):
    def __init__(
        self,
        management_controller: ManagementController,
        runtime_controller: RuntimeController,
        runtime_state: RuntimeState,
    ) -> None:
        if Qt is None:
            raise RuntimeError("PySide6 is required to build the runtime window")

        super().__init__()
        self._management_controller = management_controller
        self._runtime_controller = runtime_controller
        self._runtime_state = runtime_state
        self._management_state = self._management_controller.load_management_state()
        self._widget_host_factory = WidgetHostFactory()
        self._screen_selector: QComboBox | None = None
        self._dashboard_grid: QGridLayout | None = None
        self._touch_swipe_anchor_x: float | None = None
        self._touch_swipe_tracking = False

        self._configure_window()
        self._build_ui()
        self._apply_runtime_target()

    def _configure_window(self) -> None:
        self.setWindowTitle(f"Prox Deck {APP_RELEASE}")
        self.setMinimumSize(1200, 700)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

    def event(self, event) -> bool:  # type: ignore[override]
        if QEvent is not object and event.type() in {
            QEvent.Type.TouchBegin,
            QEvent.Type.TouchUpdate,
            QEvent.Type.TouchEnd,
            QEvent.Type.TouchCancel,
        }:
            return self._handle_touch_event(event)
        return super().event(event)

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root.setStyleSheet(
            "QWidget {"
            "background: qradialgradient(cx:0.18, cy:0.14, radius:1.2, fx:0.18, fy:0.14, "
            "stop:0 #153047, stop:0.34 #0B1520, stop:0.7 #071017, stop:1 #04070D);"
            "color: #E7F3FF;"
            "}"
            "QLabel { background: transparent; }"
            "QComboBox {"
            "background: rgba(8, 18, 28, 0.94);"
            "border: none;"
            "border-radius: 12px;"
            "padding: 8px 12px;"
            "font-weight: 700;"
            "}"
        )
        if self._is_dedicated_runtime():
            root_layout.setContentsMargins(0, 0, 0, 0)
            root_layout.setSpacing(0)
        else:
            root_layout.setContentsMargins(24, 24, 24, 24)
            root_layout.setSpacing(16)
            header_layout = QHBoxLayout()
            header_label = QLabel("Prox Deck Gauges")
            header_label.setStyleSheet(
                "font-size: 24px; font-weight: 900; letter-spacing: 0.5px; color: #F2FBFF;"
            )
            header_layout.addWidget(header_label)
            self._screen_selector = QComboBox()
            self._rebuild_screen_selector()
            self._screen_selector.currentIndexChanged.connect(self._handle_screen_change)
            header_layout.addWidget(self._screen_selector)
            root_layout.addLayout(header_layout)

        root_layout.addWidget(self._build_dashboard_view())
        self.setCentralWidget(root)
        self._select_active_screen()

    def _is_dedicated_runtime(self) -> bool:
        return self._runtime_state.runtime_target is not None

    def _build_dashboard_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        if self._is_dedicated_runtime():
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
        else:
            layout.setSpacing(14)
            subtitle = QLabel("Instrument deck with live telemetry cards and standby gauge bays.")
            subtitle.setStyleSheet("font-size: 12px; color: rgba(165, 206, 232, 0.84);")
            layout.addWidget(subtitle)

        grid_frame = QFrame()
        grid_frame.setStyleSheet(
            "QFrame {"
            "background: rgba(5, 11, 18, 0.74);"
            "border: none;"
            "border-radius: 0px;"
            "}"
        )
        grid_layout = QGridLayout(grid_frame)
        if self._is_dedicated_runtime():
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setSpacing(0)
        else:
            grid_layout.setContentsMargins(18, 18, 18, 18)
            grid_layout.setSpacing(14)
        self._configure_dashboard_grid(grid_layout)
        self._dashboard_grid = grid_layout
        layout.addWidget(grid_frame)
        self._render_runtime_screen(self._runtime_state.active_screen)
        return widget

    def _apply_runtime_target(self) -> None:
        target = self._runtime_state.runtime_target
        if target is None:
            return

        self.setGeometry(target.x, target.y, target.width, target.height)
        self.showFullScreen()

    def _select_active_screen(self) -> None:
        if self._screen_selector is None:
            return

        for index, screen in enumerate(self._runtime_state.available_screens):
            if screen.screen_id == self._runtime_state.active_screen.screen_id:
                self._screen_selector.setCurrentIndex(index)
                break

    def _handle_screen_change(self, index: int) -> None:
        if self._screen_selector is None:
            return

        screen_id = self._screen_selector.itemData(index)
        self._switch_to_screen_id(screen_id)

    def reload_runtime_state(self, runtime_state: RuntimeState) -> None:
        self._runtime_state = runtime_state
        self._management_state = self._management_controller.load_management_state()
        self._render_runtime_screen(runtime_state.active_screen)
        self._rebuild_screen_selector()

    def _render_runtime_screen(self, screen: Screen) -> None:
        if self._dashboard_grid is None:
            return

        while self._dashboard_grid.count():
            item = self._dashboard_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        occupied_cells = set()
        for instance in screen.layout.widget_instances:
            occupied_cells.update(instance.placement.cells())
            definition = self._find_widget_definition(instance.widget_id)
            widget = self._widget_host_factory.create_widget(
                instance,
                definition,
                on_widget_settings_changed=lambda instance_id, settings, screen_id=screen.screen_id: self._handle_widget_settings_changed(
                    screen_id,
                    instance_id,
                    settings,
                ),
            )
            self._prepare_widget_for_fixed_grid(widget)
            self._dashboard_grid.addWidget(
                widget,
                instance.placement.row,
                instance.placement.column,
                instance.placement.height,
                instance.placement.width,
            )

        for row in range(2):
            for column in range(3):
                if (column, row) in occupied_cells:
                    continue
                cell = _GaugeBayPlaceholder(
                    title=f"Gauge Bay {row * 3 + column + 1}",
                    percent=((row * 3 + column + 1) * 17) % 100,
                )
                self._prepare_widget_for_fixed_grid(cell)
                self._dashboard_grid.addWidget(cell, row, column)

    def _handle_widget_settings_changed(
        self,
        screen_id: str,
        instance_id: str,
        settings: dict[str, object],
    ) -> None:
        self._runtime_controller.update_widget_settings(screen_id, instance_id, settings)
        self.reload_runtime_state(self._runtime_controller.load_runtime_state())

    def _rebuild_screen_selector(self) -> None:
        if self._screen_selector is None:
            return

        current_screen_id = self._runtime_state.active_screen.screen_id
        self._screen_selector.blockSignals(True)
        self._screen_selector.clear()
        for screen in self._runtime_state.available_screens:
            label = screen.name if screen.is_available() else f"{screen.name} (Soon)"
            self._screen_selector.addItem(label, screen.screen_id)
        for index, screen in enumerate(self._runtime_state.available_screens):
            if screen.screen_id == current_screen_id:
                self._screen_selector.setCurrentIndex(index)
                break
        self._screen_selector.blockSignals(False)

    def _find_widget_definition(self, widget_id: str):
        return next(
            (
                definition
                for definition in self._management_state.widget_definitions
                if definition.widget_id == widget_id
            ),
            None,
        )

    def _configure_dashboard_grid(self, grid_layout: QGridLayout) -> None:
        for column in range(3):
            grid_layout.setColumnStretch(column, 1)
            grid_layout.setColumnMinimumWidth(column, 0)
        for row in range(2):
            grid_layout.setRowStretch(row, 1)
            grid_layout.setRowMinimumHeight(row, 0)

    def _prepare_widget_for_fixed_grid(self, widget: QWidget) -> None:
        widget.setMinimumSize(0, 0)
        if QSizePolicy is object:
            return
        widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

    def _switch_relative_screen(self, step: int) -> None:
        if not self._runtime_state.available_screens:
            return

        current_index = next(
            (
                index
                for index, screen in enumerate(self._runtime_state.available_screens)
                if screen.screen_id == self._runtime_state.active_screen.screen_id
            ),
            0,
        )
        target_index = (current_index + step) % len(self._runtime_state.available_screens)
        target_screen = self._runtime_state.available_screens[target_index]
        self._switch_to_screen_id(target_screen.screen_id)

    def _switch_to_screen_id(self, screen_id: str) -> None:
        try:
            screen = self._runtime_controller.switch_screen(screen_id)
        except ValueError:
            return

        self._runtime_state = RuntimeState(
            active_screen=screen,
            available_screens=self._runtime_state.available_screens,
            runtime_target=self._runtime_state.runtime_target,
        )
        self._render_runtime_screen(screen)
        self._select_active_screen()

    def _handle_touch_event(self, event) -> bool:
        points = event.points()
        if event.type() == QEvent.Type.TouchBegin:
            self._touch_swipe_tracking = len(points) >= 2
            self._touch_swipe_anchor_x = self._average_touch_x(points) if self._touch_swipe_tracking else None
            event.accept()
            return True

        if event.type() == QEvent.Type.TouchUpdate:
            if self._touch_swipe_tracking and len(points) >= 2 and self._touch_swipe_anchor_x is not None:
                current_x = self._average_touch_x(points)
                delta_x = current_x - self._touch_swipe_anchor_x
                if abs(delta_x) >= 120:
                    self._switch_relative_screen(-1 if delta_x > 0 else 1)
                    self._touch_swipe_tracking = False
                    self._touch_swipe_anchor_x = None
            event.accept()
            return True

        self._touch_swipe_tracking = False
        self._touch_swipe_anchor_x = None
        event.accept()
        return True

    @staticmethod
    def _average_touch_x(points) -> float:
        total = 0.0
        for point in points:
            position = point.position()
            if isinstance(position, QPointF):
                total += position.x()
            else:
                total += position.x()
        return total / len(points)


class _GaugeBayPlaceholder(QWidget):
    def __init__(self, title: str, percent: int) -> None:
        super().__init__()
        self._title = title
        self._percent = percent
        self.setMinimumHeight(180)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        if QPainter is object:
            return super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(6, 6, -6, -6)

        shell_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        shell_gradient.setColorAt(0.0, QColor(7, 15, 24, 242))
        shell_gradient.setColorAt(1.0, QColor(4, 8, 14, 248))
        painter.setBrush(shell_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)

        dial_rect = rect.adjusted(26, 22, -26, -54)
        dial_size = min(dial_rect.width(), dial_rect.height())
        dial_rect.setWidth(dial_size)
        dial_rect.setHeight(dial_size)
        dial_rect.moveCenter(dial_rect.center())

        glow = QRadialGradient(dial_rect.center().x(), dial_rect.center().y(), dial_size * 0.62)
        glow.setColorAt(0.0, QColor(92, 210, 255, 54))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(dial_rect.adjusted(-8, -8, 8, 8))

        painter.setBrush(QColor(5, 12, 20, 218))
        painter.setPen(QPen(QColor(80, 155, 196, 52), 2))
        painter.drawEllipse(dial_rect)

        ring_rect = dial_rect.adjusted(10, 10, -10, -10)
        ring_gradient = QConicalGradient(ring_rect.center().x(), ring_rect.center().y(), -120)
        ring_gradient.setColorAt(0.0, QColor("#6BE8FF"))
        ring_gradient.setColorAt(0.38, QColor("#1B95FF"))
        ring_gradient.setColorAt(0.72, QColor("#7AF4FF"))
        ring_gradient.setColorAt(1.0, QColor("#6BE8FF"))
        painter.setPen(QPen(QColor(40, 71, 88, 188), 10))
        painter.drawArc(ring_rect, 35 * 16, 290 * 16)
        painter.setPen(QPen(ring_gradient, 10))
        painter.drawArc(ring_rect, 35 * 16, int(-(290 * (self._percent / 100.0)) * 16))

        inner_rect = ring_rect.adjusted(18, 18, -18, -18)
        painter.setBrush(QColor(8, 16, 25, 228))
        painter.setPen(QPen(QColor(97, 184, 221, 38), 1))
        painter.drawEllipse(inner_rect)

        for tick in range(7):
            angle = 35 + (290 / 6) * tick
            self._draw_tick(painter, ring_rect, angle)

        title_font = painter.font()
        title_font.setPointSize(9)
        if QFont is not object:
            title_font.setWeight(QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(122, 202, 235))
        painter.drawText(rect.adjusted(14, 10, -14, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self._title.upper())

        value_font = painter.font()
        value_font.setPointSize(24)
        if QFont is not object:
            value_font.setWeight(QFont.Weight.ExtraBold)
        painter.setFont(value_font)
        painter.setPen(QColor(234, 248, 255))
        painter.drawText(inner_rect, Qt.AlignmentFlag.AlignCenter, f"{self._percent}%")

        detail_font = painter.font()
        detail_font.setPointSize(8)
        if QFont is not object:
            detail_font.setWeight(QFont.Weight.Bold)
        painter.setFont(detail_font)
        painter.setPen(QColor(110, 174, 203))
        painter.drawText(rect.adjusted(14, 0, -14, -14), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, "STANDBY INSTRUMENT")

    def _draw_tick(self, painter: QPainter, rect, angle_degrees: float) -> None:
        import math

        angle_radians = math.radians(angle_degrees - 90)
        center_x = rect.center().x()
        center_y = rect.center().y()
        outer_radius = rect.width() / 2
        inner_radius = outer_radius - 12
        start_x = center_x + math.cos(angle_radians) * inner_radius
        start_y = center_y + math.sin(angle_radians) * inner_radius
        end_x = center_x + math.cos(angle_radians) * outer_radius
        end_y = center_y + math.sin(angle_radians) * outer_radius
        painter.setPen(QPen(QColor(116, 187, 220, 102), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))
