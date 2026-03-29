from __future__ import annotations

from dataclasses import dataclass

from proxdeck.application.controllers.management_controller import ManagementController
from proxdeck.application.controllers.runtime_controller import RuntimeController
from proxdeck.application.dto.management_state import ManagementState
from proxdeck.application.dto.runtime_state import RuntimeState
from proxdeck.domain.models.screen import Screen
from proxdeck.presentation.widgets.widget_host_factory import WidgetHostFactory

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    Qt = None
    QCheckBox = object
    QComboBox = object
    QFrame = object
    QGridLayout = object
    QHBoxLayout = object
    QLabel = object
    QLineEdit = object
    QListWidget = object
    QListWidgetItem = object
    QMainWindow = object
    QMessageBox = object
    QPushButton = object
    QSpinBox = object
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
        self._management_screen_selector: QComboBox | None = None
        self._management_widget_selector: QComboBox | None = None
        self._widget_instance_list: QListWidget | None = None
        self._web_url_input: QLineEdit | None = None
        self._web_mobile_checkbox: QCheckBox | None = None
        self._column_input: QSpinBox | None = None
        self._row_input: QSpinBox | None = None
        self._width_input: QSpinBox | None = None
        self._height_input: QSpinBox | None = None
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
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.addWidget(QLabel("Management mode"))

        self._management_screen_selector = QComboBox()
        for screen in self._management_state.screens:
            label = screen.name if screen.is_available() else f"{screen.name} (Soon)"
            self._management_screen_selector.addItem(label, screen.screen_id)
        self._management_screen_selector.currentIndexChanged.connect(
            self._refresh_management_instances
        )
        layout.addWidget(self._management_screen_selector)

        self._management_widget_selector = QComboBox()
        for definition in self._management_state.widget_definitions:
            self._management_widget_selector.addItem(
                definition.display_name,
                definition.widget_id,
            )
        layout.addWidget(self._management_widget_selector)

        placement_layout = QHBoxLayout()
        self._column_input = self._build_spin_box(0, 2)
        self._row_input = self._build_spin_box(0, 1)
        self._width_input = self._build_spin_box(1, 3)
        self._height_input = self._build_spin_box(1, 2)
        placement_layout.addWidget(QLabel("Col"))
        placement_layout.addWidget(self._column_input)
        placement_layout.addWidget(QLabel("Row"))
        placement_layout.addWidget(self._row_input)
        placement_layout.addWidget(QLabel("Width"))
        placement_layout.addWidget(self._width_input)
        placement_layout.addWidget(QLabel("Height"))
        placement_layout.addWidget(self._height_input)
        layout.addLayout(placement_layout)

        add_button = QPushButton("Add Widget")
        add_button.clicked.connect(self._handle_add_widget)
        layout.addWidget(add_button)

        self._widget_instance_list = QListWidget()
        self._widget_instance_list.currentItemChanged.connect(self._load_web_widget_settings)
        layout.addWidget(self._widget_instance_list)

        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self._handle_remove_widget)
        layout.addWidget(remove_button)

        self._web_url_input = QLineEdit()
        self._web_url_input.setPlaceholderText("https://example.com")
        self._web_mobile_checkbox = QCheckBox("Force mobile view")
        layout.addWidget(QLabel("Web widget configuration"))
        layout.addWidget(self._web_url_input)
        layout.addWidget(self._web_mobile_checkbox)

        save_web_button = QPushButton("Save Web Settings")
        save_web_button.clicked.connect(self._handle_save_web_settings)
        layout.addWidget(save_web_button)

        self._refresh_management_instances()
        return widget

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

    def _build_spin_box(self, minimum: int, maximum: int) -> QSpinBox:
        spin_box = QSpinBox()
        spin_box.setRange(minimum, maximum)
        return spin_box

    def _show_management_mode(self) -> None:
        if self._content_stack is not None:
            self._content_stack.setCurrentIndex(1)

    def _show_runtime_mode(self) -> None:
        if self._content_stack is not None:
            self._content_stack.setCurrentIndex(0)

    def _refresh_management_state(self) -> None:
        self._management_state = self._management_controller.load_management_state()

    def _refresh_management_instances(self, *_args) -> None:
        if self._management_screen_selector is None or self._widget_instance_list is None:
            return

        self._refresh_management_state()
        self._widget_instance_list.clear()
        screen_id = self._management_screen_selector.currentData()
        screen = next(
            (item for item in self._management_state.screens if item.screen_id == screen_id),
            None,
        )
        if screen is None:
            return

        for instance in screen.layout.widget_instances:
            item = QListWidgetItem(
                f"{instance.widget_id} @ ({instance.placement.column}, {instance.placement.row}) "
                f"{instance.placement.width}x{instance.placement.height}"
            )
            item.setData(Qt.ItemDataRole.UserRole, instance.instance_id)
            self._widget_instance_list.addItem(item)

    def _handle_add_widget(self) -> None:
        if (
            self._management_screen_selector is None
            or self._management_widget_selector is None
            or self._column_input is None
            or self._row_input is None
            or self._width_input is None
            or self._height_input is None
        ):
            return

        try:
            self._management_controller.add_widget_instance(
                screen_id=self._management_screen_selector.currentData(),
                widget_id=self._management_widget_selector.currentData(),
                column=self._column_input.value(),
                row=self._row_input.value(),
                width=self._width_input.value(),
                height=self._height_input.value(),
            )
        except ValueError as error:
            QMessageBox.warning(self, "Widget placement rejected", str(error))
            return

        self._refresh_management_instances()
        self._refresh_runtime_after_management()

    def _handle_remove_widget(self) -> None:
        if self._management_screen_selector is None or self._widget_instance_list is None:
            return

        current_item = self._widget_instance_list.currentItem()
        if current_item is None:
            return

        try:
            self._management_controller.remove_widget_instance(
                screen_id=self._management_screen_selector.currentData(),
                instance_id=current_item.data(Qt.ItemDataRole.UserRole),
            )
        except ValueError as error:
            QMessageBox.warning(self, "Widget removal failed", str(error))
            return

        self._refresh_management_instances()
        self._refresh_runtime_after_management()

    def _load_web_widget_settings(self, *_args) -> None:
        if (
            self._management_screen_selector is None
            or self._widget_instance_list is None
            or self._web_url_input is None
            or self._web_mobile_checkbox is None
        ):
            return

        current_item = self._widget_instance_list.currentItem()
        if current_item is None:
            self._web_url_input.clear()
            self._web_mobile_checkbox.setChecked(False)
            return

        screen_id = self._management_screen_selector.currentData()
        instance_id = current_item.data(Qt.ItemDataRole.UserRole)
        screen = next(
            (item for item in self._management_state.screens if item.screen_id == screen_id),
            None,
        )
        if screen is None:
            return

        instance = next(
            (item for item in screen.layout.widget_instances if item.instance_id == instance_id),
            None,
        )
        if instance is None or instance.widget_id != "web":
            self._web_url_input.clear()
            self._web_mobile_checkbox.setChecked(False)
            return

        self._web_url_input.setText(str(instance.settings.get("url", "")))
        self._web_mobile_checkbox.setChecked(bool(instance.settings.get("force_mobile", False)))

    def _handle_save_web_settings(self) -> None:
        if (
            self._management_screen_selector is None
            or self._widget_instance_list is None
            or self._web_url_input is None
            or self._web_mobile_checkbox is None
        ):
            return

        current_item = self._widget_instance_list.currentItem()
        if current_item is None:
            return

        try:
            self._management_controller.configure_web_widget(
                screen_id=self._management_screen_selector.currentData(),
                instance_id=current_item.data(Qt.ItemDataRole.UserRole),
                url=self._web_url_input.text(),
                force_mobile=self._web_mobile_checkbox.isChecked(),
            )
        except ValueError as error:
            QMessageBox.warning(self, "Web widget configuration failed", str(error))
            return

        self._refresh_management_instances()
        self._refresh_runtime_after_management()

    def _refresh_runtime_after_management(self) -> None:
        self._management_state = self._management_controller.load_management_state()
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
            widget = self._widget_host_factory.create_widget(instance)
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
