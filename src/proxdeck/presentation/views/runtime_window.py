from __future__ import annotations

from proxdeck.application.controllers.management_controller import ManagementController
from proxdeck.application.controllers.runtime_controller import RuntimeController
from proxdeck.application.dto.runtime_state import RuntimeState
from proxdeck.domain.models.screen import Screen
from proxdeck.presentation.widgets.widget_host_factory import WidgetHostFactory

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QComboBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    Qt = None
    QComboBox = object
    QFrame = object
    QGridLayout = object
    QHBoxLayout = object
    QLabel = object
    QMainWindow = object
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

        self._configure_window()
        self._build_ui()
        self._apply_runtime_target()

    def _configure_window(self) -> None:
        self.setWindowTitle("Prox Deck")
        self.setMinimumSize(1200, 700)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        if self._is_dedicated_runtime():
            root_layout.setContentsMargins(0, 0, 0, 0)
            root_layout.setSpacing(0)
        else:
            root_layout.setContentsMargins(24, 24, 24, 24)
            root_layout.setSpacing(16)
            header_layout = QHBoxLayout()
            header_layout.addWidget(QLabel("Prox Deck Runtime"))
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
            layout.setSpacing(12)
            layout.addWidget(QLabel("Runtime Dashboard"))

        grid_frame = QFrame()
        grid_layout = QGridLayout(grid_frame)
        if self._is_dedicated_runtime():
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setSpacing(0)
        else:
            grid_layout.setSpacing(12)
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
                cell = QLabel(f"Empty cell {row * 3 + column + 1}")
                cell.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setStyleSheet(
                    "QLabel {"
                    "color: #8CA0B3;"
                    "background: #17202B;"
                    "border: 1px dashed #415062;"
                    "border-radius: 12px;"
                    "padding: 12px;"
                    "}"
                )
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
