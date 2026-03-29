from __future__ import annotations

from dataclasses import dataclass

from proxdeck.application.controllers.management_controller import ManagementController
from proxdeck.application.dto.management_state import ManagementState
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.value_objects.widget_size import SIZE_PRESET_DIMENSIONS, WidgetSize
from proxdeck.presentation.views.widget_definition_summary import (
    format_widget_definition_summary,
)

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    Qt = None
    QCheckBox = object
    QComboBox = object
    QHBoxLayout = object
    QLabel = object
    QLineEdit = object
    QListWidget = object
    QListWidgetItem = object
    QMessageBox = object
    QPushButton = object
    QSpinBox = object
    QVBoxLayout = object
    QWidget = object


@dataclass(frozen=True)
class ManagementScreenUiState:
    editable: bool
    status_text: str


class ManagementView(QWidget):
    def __init__(self, management_controller: ManagementController) -> None:
        if Qt is None:
            raise RuntimeError("PySide6 is required to build the management view")

        super().__init__()
        self._management_controller = management_controller
        self._management_state = self._management_controller.load_management_state()
        self._management_screen_selector: QComboBox | None = None
        self._management_widget_selector: QComboBox | None = None
        self._size_preset_selector: QComboBox | None = None
        self._widget_instance_list: QListWidget | None = None
        self._web_url_input: QLineEdit | None = None
        self._web_mobile_checkbox: QCheckBox | None = None
        self._column_input: QSpinBox | None = None
        self._row_input: QSpinBox | None = None
        self._width_input: QSpinBox | None = None
        self._height_input: QSpinBox | None = None
        self._definition_metadata_label: QLabel | None = None
        self._instance_metadata_label: QLabel | None = None
        self._management_status_label: QLabel | None = None
        self._add_widget_button: QPushButton | None = None
        self._suggest_placement_button: QPushButton | None = None
        self._remove_widget_button: QPushButton | None = None
        self._save_web_button: QPushButton | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
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
        self._management_widget_selector.currentIndexChanged.connect(
            self._refresh_definition_metadata
        )
        layout.addWidget(self._management_widget_selector)

        self._size_preset_selector = QComboBox()
        for preset in SIZE_PRESET_DIMENSIONS:
            self._size_preset_selector.addItem(preset, preset)
        self._size_preset_selector.currentIndexChanged.connect(self._apply_selected_size_preset)
        layout.addWidget(self._size_preset_selector)

        self._definition_metadata_label = QLabel()
        self._definition_metadata_label.setWordWrap(True)
        layout.addWidget(self._definition_metadata_label)

        self._management_status_label = QLabel()
        self._management_status_label.setWordWrap(True)
        layout.addWidget(self._management_status_label)

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

        self._add_widget_button = QPushButton("Add Widget")
        self._add_widget_button.clicked.connect(self._handle_add_widget)
        layout.addWidget(self._add_widget_button)

        self._suggest_placement_button = QPushButton("Suggest Placement")
        self._suggest_placement_button.clicked.connect(self._handle_suggest_placement)
        layout.addWidget(self._suggest_placement_button)

        self._widget_instance_list = QListWidget()
        self._widget_instance_list.currentItemChanged.connect(self._load_web_widget_settings)
        layout.addWidget(self._widget_instance_list)

        self._instance_metadata_label = QLabel()
        self._instance_metadata_label.setWordWrap(True)
        layout.addWidget(self._instance_metadata_label)

        self._remove_widget_button = QPushButton("Remove Selected")
        self._remove_widget_button.clicked.connect(self._handle_remove_widget)
        layout.addWidget(self._remove_widget_button)

        self._web_url_input = QLineEdit()
        self._web_url_input.setPlaceholderText("https://example.com")
        self._web_mobile_checkbox = QCheckBox("Force mobile view")
        layout.addWidget(QLabel("Web widget configuration"))
        layout.addWidget(self._web_url_input)
        layout.addWidget(self._web_mobile_checkbox)

        self._save_web_button = QPushButton("Save Web Settings")
        self._save_web_button.clicked.connect(self._handle_save_web_settings)
        layout.addWidget(self._save_web_button)

        self._refresh_management_instances()
        self._apply_selected_size_preset()
        self._refresh_definition_metadata()

    def _build_spin_box(self, minimum: int, maximum: int) -> QSpinBox:
        spin_box = QSpinBox()
        spin_box.setRange(minimum, maximum)
        return spin_box

    def refresh(self) -> None:
        self._refresh_management_state()
        self._refresh_management_instances()
        self._refresh_definition_metadata()

    def _refresh_management_state(self) -> None:
        self._management_state = self._management_controller.load_management_state()

    def _refresh_management_instances(self, *_args) -> None:
        if self._management_screen_selector is None or self._widget_instance_list is None:
            return

        self._refresh_management_state()
        self._widget_instance_list.clear()
        screen = self._current_screen()
        if screen is None:
            return

        self._apply_screen_state(screen)
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
            or self._size_preset_selector is None
            or self._column_input is None
            or self._row_input is None
        ):
            return

        try:
            self._management_controller.add_widget_instance_from_preset(
                screen_id=self._management_screen_selector.currentData(),
                widget_id=self._management_widget_selector.currentData(),
                column=self._column_input.value(),
                row=self._row_input.value(),
                size_preset=self._size_preset_selector.currentData(),
            )
        except ValueError as error:
            QMessageBox.warning(self, "Widget placement rejected", str(error))
            return

        self.refresh()

    def _handle_suggest_placement(self) -> None:
        if (
            self._management_screen_selector is None
            or self._management_widget_selector is None
            or self._size_preset_selector is None
            or self._column_input is None
            or self._row_input is None
        ):
            return

        try:
            placement = self._management_controller.suggest_placement_for_preset(
                screen_id=self._management_screen_selector.currentData(),
                widget_id=self._management_widget_selector.currentData(),
                size_preset=self._size_preset_selector.currentData(),
            )
        except ValueError as error:
            QMessageBox.warning(self, "Placement suggestion failed", str(error))
            return

        if placement is None:
            QMessageBox.warning(
                self,
                "No placement available",
                "No valid placement is available for the selected widget size.",
            )
            return

        self._column_input.setValue(placement.column)
        self._row_input.setValue(placement.row)

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

        self.refresh()

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
            self._refresh_instance_metadata(None)
            return

        screen = self._current_screen()
        if screen is None:
            return

        instance_id = current_item.data(Qt.ItemDataRole.UserRole)
        instance = next(
            (item for item in screen.layout.widget_instances if item.instance_id == instance_id),
            None,
        )
        if instance is None or instance.widget_id != "web":
            self._web_url_input.clear()
            self._web_mobile_checkbox.setChecked(False)
            self._refresh_instance_metadata(instance)
            return

        self._web_url_input.setText(str(instance.settings.get("url", "")))
        self._web_mobile_checkbox.setChecked(bool(instance.settings.get("force_mobile", False)))
        self._refresh_instance_metadata(instance)

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

        self.refresh()

    def _apply_selected_size_preset(self, *_args) -> None:
        if (
            self._size_preset_selector is None
            or self._width_input is None
            or self._height_input is None
        ):
            return

        preset = self._size_preset_selector.currentData()
        _, width, height = WidgetSize.from_preset(preset)
        self._width_input.setValue(width)
        self._height_input.setValue(height)

    def _refresh_definition_metadata(self, *_args) -> None:
        if self._management_widget_selector is None or self._definition_metadata_label is None:
            return

        definition = self._find_widget_definition(self._management_widget_selector.currentData())
        if definition is None:
            self._definition_metadata_label.setText("No widget definition selected.")
            return

        self._definition_metadata_label.setText(format_widget_definition_summary(definition))

    def _refresh_instance_metadata(self, instance) -> None:
        if self._instance_metadata_label is None:
            return

        if instance is None:
            self._instance_metadata_label.setText("No widget instance selected.")
            return

        definition = self._find_widget_definition(instance.widget_id)
        if definition is None:
            self._instance_metadata_label.setText(
                f"Selected instance\nID: {instance.instance_id}\nDefinition metadata unavailable."
            )
            return

        self._instance_metadata_label.setText(
            "Selected widget instance\n"
            f"Instance: {instance.instance_id}\n"
            f"Widget: {definition.display_name}\n"
            f"Entrypoint: {definition.entrypoint}\n"
            f"Distribution: {definition.install_metadata.distribution}\n"
            f"Installation scope: {definition.install_metadata.installation_scope}"
        )

    def _find_widget_definition(self, widget_id: str):
        return next(
            (
                definition
                for definition in self._management_state.widget_definitions
                if definition.widget_id == widget_id
            ),
            None,
        )

    def _current_screen(self) -> Screen | None:
        if self._management_screen_selector is None:
            return None

        screen_id = self._management_screen_selector.currentData()
        return next(
            (item for item in self._management_state.screens if item.screen_id == screen_id),
            None,
        )

    def _apply_screen_state(self, screen: Screen) -> None:
        ui_state = self.build_screen_ui_state(screen)
        for widget in (
            self._management_widget_selector,
            self._size_preset_selector,
            self._column_input,
            self._row_input,
            self._width_input,
            self._height_input,
            self._widget_instance_list,
            self._web_url_input,
            self._web_mobile_checkbox,
            self._add_widget_button,
            self._suggest_placement_button,
            self._remove_widget_button,
            self._save_web_button,
        ):
            if widget is not None:
                widget.setEnabled(ui_state.editable)

        if self._management_status_label is not None:
            self._management_status_label.setText(ui_state.status_text)

        if not ui_state.editable:
            if self._web_url_input is not None:
                self._web_url_input.clear()
            if self._web_mobile_checkbox is not None:
                self._web_mobile_checkbox.setChecked(False)
            self._refresh_instance_metadata(None)

    @staticmethod
    def build_screen_ui_state(screen: Screen) -> ManagementScreenUiState:
        if screen.is_available():
            return ManagementScreenUiState(editable=True, status_text=f"{screen.name} is editable.")
        if screen.availability.value == "soon":
            return ManagementScreenUiState(
                editable=False,
                status_text=f"{screen.name} is not editable yet. This screen is marked Soon.",
            )
        return ManagementScreenUiState(
            editable=False,
            status_text=f"{screen.name} is locked and not editable.",
        )
