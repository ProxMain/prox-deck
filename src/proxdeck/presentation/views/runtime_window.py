from __future__ import annotations

from dataclasses import dataclass

from proxdeck.application.controllers.management_controller import ManagementController
from proxdeck.application.controllers.runtime_controller import RuntimeController
from proxdeck.application.dto.runtime_state import RuntimeState
from proxdeck.domain.models.screen import Screen
from proxdeck.presentation.views.management_view import ManagementView
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
        QPushButton,
        QStackedWidget,
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
    QPushButton = object
    QStackedWidget = object
    QVBoxLayout = object
    QWidget = object


@dataclass(frozen=True)
class RuntimeBanner:
    headline: str
    detail: str


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
        self._screen_banner: QLabel | None = None
        self._content_stack: QStackedWidget | None = None
        self._dashboard_grid: QGridLayout | None = None
        self._management_view: ManagementView | None = None

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
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Prox Deck Runtime"))
        self._screen_selector = QComboBox()
        for screen in self._runtime_state.available_screens:
            label = screen.name
            if not screen.is_available():
                label = f"{label} (Soon)"
            self._screen_selector.addItem(label, screen.screen_id)
        self._screen_selector.currentIndexChanged.connect(self._handle_screen_change)
        header_layout.addWidget(self._screen_selector)

        manage_button = QPushButton("Management")
        manage_button.clicked.connect(self._show_management_mode)
        header_layout.addWidget(manage_button)
        runtime_button = QPushButton("Runtime")
        runtime_button.clicked.connect(self._show_runtime_mode)
        header_layout.addWidget(runtime_button)
        root_layout.addLayout(header_layout)

        banner = self._create_runtime_banner()
        self._screen_banner = QLabel(f"{banner.headline}\n{banner.detail}")
        root_layout.addWidget(self._screen_banner)

        self._content_stack = QStackedWidget()
        self._content_stack.addWidget(self._build_dashboard_view())
        self._content_stack.addWidget(self._build_management_view())
        root_layout.addWidget(self._content_stack)

        self.setCentralWidget(root)
        self._select_active_screen()

    def _build_dashboard_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.addWidget(QLabel("Runtime Dashboard"))

        grid_frame = QFrame()
        grid_layout = QGridLayout(grid_frame)
        grid_layout.setSpacing(12)
        self._dashboard_grid = grid_layout
        layout.addWidget(grid_frame)
        self._render_runtime_screen(self._runtime_state.active_screen)
        return widget

    def _build_management_view(self) -> QWidget:
        self._management_view = ManagementView(self._management_controller)
        return self._management_view

    def _create_runtime_banner(self) -> RuntimeBanner:
        if self._runtime_state.runtime_target is None:
            return RuntimeBanner(
                headline="Edge target not detected",
                detail="Runtime stays in a safe windowed fallback instead of fullscreen on the wrong monitor.",
            )

        target = self._runtime_state.runtime_target
        return RuntimeBanner(
            headline=f"Runtime target: {target.monitor_name}",
            detail=f"Detected resolution {target.width}x{target.height} at ({target.x}, {target.y}).",
        )

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
        if self._screen_selector is None or self._screen_banner is None:
            return

        screen_id = self._screen_selector.itemData(index)
        try:
            screen = self._runtime_controller.switch_screen(screen_id)
        except ValueError as error:
            self._screen_banner.setText(str(error))
            return

        self._runtime_state = RuntimeState(
            active_screen=screen,
            available_screens=self._runtime_state.available_screens,
            runtime_target=self._runtime_state.runtime_target,
        )
        self._render_runtime_screen(screen)
        self._screen_banner.setText(f"{screen.name}\n{screen.availability.value.title()} profile loaded.")

    def _show_management_mode(self) -> None:
        if self._content_stack is not None:
            self._content_stack.setCurrentIndex(1)

    def _show_runtime_mode(self) -> None:
        if self._content_stack is not None:
            self._content_stack.setCurrentIndex(0)

    def _refresh_runtime_after_management(self) -> None:
        self._management_state = self._management_controller.load_management_state()
        if self._management_view is not None:
            self._management_view.refresh()
        active_screen = next(
            (
                screen
                for screen in self._management_state.screens
                if screen.screen_id == self._runtime_state.active_screen.screen_id
            ),
            None,
        )
        if active_screen is None:
            return

        self._runtime_state = RuntimeState(
            active_screen=active_screen,
            available_screens=tuple(self._management_state.screens),
            runtime_target=self._runtime_state.runtime_target,
        )
        self._render_runtime_screen(active_screen)

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
            widget = self._widget_host_factory.create_widget(instance, definition)
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
