from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from proxdeck.application.controllers.management_controller import ManagementController
from proxdeck.application.dto.management_state import ManagementState
from proxdeck.domain.models.screen import Screen
from proxdeck.domain.value_objects.widget_size import SIZE_PRESET_DIMENSIONS, WidgetSize
from proxdeck.presentation.views.layout_preview import LayoutPreviewWidget
from proxdeck.presentation.views.widget_palette import WidgetPaletteView
from proxdeck.presentation.views.widget_definition_summary import (
    format_widget_definition_summary,
)
from proxdeck.presentation.widgets.widget_host_factory import WidgetHostFactory

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFormLayout,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    Qt = None
    QCheckBox = object
    QComboBox = object
    QFormLayout = object
    QFrame = object
    QGridLayout = object
    QGroupBox = object
    QHBoxLayout = object
    QLabel = object
    QLineEdit = object
    QListWidget = object
    QListWidgetItem = object
    QMessageBox = object
    QPushButton = object
    QScrollArea = object
    QSpinBox = object
    QVBoxLayout = object
    QWidget = object


@dataclass(frozen=True)
class ManagementScreenUiState:
    editable: bool
    status_text: str


class ManagementView(QWidget):
    def __init__(
        self,
        management_controller: ManagementController,
        on_state_changed: Callable[[], None] | None = None,
    ) -> None:
        if Qt is None:
            raise RuntimeError("PySide6 is required to build the management view")

        super().__init__()
        self._management_controller = management_controller
        self._on_state_changed = on_state_changed
        self._management_state = self._management_controller.load_management_state()
        self._widget_host_factory = WidgetHostFactory()
        self._management_screen_selector: QComboBox | None = None
        self._management_widget_selector: QComboBox | None = None
        self._size_preset_selector: QComboBox | None = None
        self._widget_palette: WidgetPaletteView | None = None
        self._widget_instance_list: QListWidget | None = None
        self._web_url_input: QLineEdit | None = None
        self._web_mobile_checkbox: QCheckBox | None = None
        self._launcher_label_inputs: list[QLineEdit] = []
        self._launcher_target_inputs: list[QLineEdit] = []
        self._layout_preview: LayoutPreviewWidget | None = None
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
        self._save_launcher_button: QPushButton | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title_label = QLabel("Configuration")
        title_label.setStyleSheet("font-size: 24px; font-weight: 700; color: #EAF0F6;")
        layout.addWidget(title_label)

        subtitle_label = QLabel(
            "Manage screens, place widgets, and configure widget-specific behavior."
        )
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("font-size: 13px; color: #8FA3B7;")
        layout.addWidget(subtitle_label)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        layout.addLayout(content_layout, 1)

        left_column = QVBoxLayout()
        left_column.setSpacing(16)
        right_column = QVBoxLayout()
        right_column.setSpacing(16)
        content_layout.addLayout(left_column, 3)
        content_layout.addLayout(right_column, 2)

        selection_card = self._build_section_card("Screen & Palette")
        selection_layout = QVBoxLayout(selection_card)
        selection_layout.setSpacing(10)

        self._management_screen_selector = QComboBox()
        for screen in self._management_state.screens:
            label = screen.name if screen.is_available() else f"{screen.name} (Soon)"
            self._management_screen_selector.addItem(label, screen.screen_id)
        self._management_screen_selector.currentIndexChanged.connect(
            self._refresh_management_instances
        )
        selection_layout.addWidget(QLabel("Screen"))
        selection_layout.addWidget(self._management_screen_selector)

        self._management_widget_selector = QComboBox()
        for definition in self._management_state.widget_definitions:
            self._management_widget_selector.addItem(
                definition.display_name,
                definition.widget_id,
        )
        self._management_widget_selector.currentIndexChanged.connect(
            self._refresh_definition_metadata
        )
        self._management_widget_selector.hide()

        self._size_preset_selector = QComboBox()
        for preset in SIZE_PRESET_DIMENSIONS:
            self._size_preset_selector.addItem(preset, preset)
        self._size_preset_selector.currentIndexChanged.connect(self._apply_selected_size_preset)
        self._size_preset_selector.hide()

        palette_label = QLabel("Widget Palette")
        palette_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #EAF0F6;")
        selection_layout.addWidget(palette_label)
        self._widget_palette = WidgetPaletteView(on_select_widget=self._handle_palette_select)
        selection_layout.addWidget(self._widget_palette)

        self._definition_metadata_label = QLabel()
        self._definition_metadata_label.setWordWrap(True)
        self._definition_metadata_label.setStyleSheet("color: #C8D3DE;")
        selection_layout.addWidget(self._definition_metadata_label)

        left_column.addWidget(selection_card)

        status_card = self._build_section_card("Screen Status")
        status_layout = QVBoxLayout(status_card)
        status_layout.setSpacing(8)
        self._management_status_label = QLabel()
        self._management_status_label.setWordWrap(True)
        self._management_status_label.setStyleSheet("color: #D7E2EC;")
        status_layout.addWidget(self._management_status_label)
        left_column.addWidget(status_card)

        placement_card = self._build_section_card("Placement & Add")
        placement_layout = QGridLayout(placement_card)
        placement_layout.setHorizontalSpacing(10)
        placement_layout.setVerticalSpacing(10)
        self._column_input = self._build_spin_box(0, 2)
        self._row_input = self._build_spin_box(0, 1)
        self._width_input = self._build_spin_box(1, 3)
        self._height_input = self._build_spin_box(1, 2)
        placement_layout.addWidget(QLabel("Column"), 0, 0)
        placement_layout.addWidget(self._column_input, 0, 1)
        placement_layout.addWidget(QLabel("Row"), 0, 2)
        placement_layout.addWidget(self._row_input, 0, 3)
        placement_layout.addWidget(QLabel("Width"), 1, 0)
        placement_layout.addWidget(self._width_input, 1, 1)
        placement_layout.addWidget(QLabel("Height"), 1, 2)
        placement_layout.addWidget(self._height_input, 1, 3)

        self._add_widget_button = QPushButton("Add Widget")
        self._add_widget_button.clicked.connect(self._handle_add_widget)
        self._suggest_placement_button = QPushButton("Suggest Placement")
        self._suggest_placement_button.clicked.connect(self._handle_suggest_placement)
        placement_layout.addWidget(self._suggest_placement_button, 2, 0, 1, 2)
        placement_layout.addWidget(self._add_widget_button, 2, 2, 1, 2)
        left_column.addWidget(placement_card)

        instances_card = self._build_section_card("Widget Instances")
        instances_layout = QVBoxLayout(instances_card)
        instances_layout.setSpacing(10)
        self._layout_preview = LayoutPreviewWidget(
            on_move_instance=self._handle_preview_move,
            on_resize_instance=self._handle_preview_resize,
            on_select_instance=self._handle_preview_select,
            on_add_widget=self._handle_preview_add,
            render_widget_preview=lambda instance, definition: self._widget_host_factory.create_widget(
                instance,
                definition,
            ),
        )
        instances_layout.addWidget(self._layout_preview)
        self._widget_instance_list = QListWidget()
        self._widget_instance_list.currentItemChanged.connect(self._load_web_widget_settings)
        self._widget_instance_list.setMinimumHeight(220)
        instances_layout.addWidget(self._widget_instance_list)

        self._instance_metadata_label = QLabel()
        self._instance_metadata_label.setWordWrap(True)
        self._instance_metadata_label.setStyleSheet("color: #C8D3DE;")
        instances_layout.addWidget(self._instance_metadata_label)

        self._remove_widget_button = QPushButton("Remove Selected")
        self._remove_widget_button.clicked.connect(self._handle_remove_widget)
        instances_layout.addWidget(self._remove_widget_button)
        left_column.addWidget(instances_card, 1)

        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setFrameShape(QFrame.Shape.NoFrame)
        config_container = QWidget()
        config_layout = QVBoxLayout(config_container)
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_layout.setSpacing(16)
        config_scroll.setWidget(config_container)
        right_column.addWidget(config_scroll, 1)

        web_card = self._build_section_card("Web Widget")
        web_layout = QVBoxLayout(web_card)
        web_layout.setSpacing(10)
        self._web_url_input = QLineEdit()
        self._web_url_input.setPlaceholderText("https://example.com")
        self._web_mobile_checkbox = QCheckBox("Force mobile view")
        web_layout.addWidget(QLabel("URL"))
        web_layout.addWidget(self._web_url_input)
        web_layout.addWidget(self._web_mobile_checkbox)

        self._save_web_button = QPushButton("Save Web Settings")
        self._save_web_button.clicked.connect(self._handle_save_web_settings)
        web_layout.addWidget(self._save_web_button)
        config_layout.addWidget(web_card)

        launcher_card = self._build_section_card("Launcher")
        launcher_layout = QVBoxLayout(launcher_card)
        launcher_layout.setSpacing(10)
        launcher_hint = QLabel("Configure up to four quick actions for the selected launcher.")
        launcher_hint.setWordWrap(True)
        launcher_hint.setStyleSheet("font-size: 12px; color: #8FA3B7;")
        launcher_layout.addWidget(launcher_hint)
        launcher_form = QFormLayout()
        launcher_form.setHorizontalSpacing(10)
        launcher_form.setVerticalSpacing(8)
        for index in range(4):
            label_input = QLineEdit()
            label_input.setPlaceholderText(f"Action {index + 1} label")
            target_input = QLineEdit()
            target_input.setPlaceholderText(f"Action {index + 1} target")
            self._launcher_label_inputs.append(label_input)
            self._launcher_target_inputs.append(target_input)
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            row_layout.addWidget(label_input, 1)
            row_layout.addWidget(target_input, 2)
            launcher_form.addRow(f"Action {index + 1}", row_widget)
        launcher_layout.addLayout(launcher_form)

        self._save_launcher_button = QPushButton("Save Launcher Settings")
        self._save_launcher_button.clicked.connect(self._handle_save_launcher_settings)
        launcher_layout.addWidget(self._save_launcher_button)
        config_layout.addWidget(launcher_card)
        config_layout.addStretch(1)

        self._refresh_management_instances()
        self._apply_selected_size_preset()
        self._refresh_definition_metadata()
        self._refresh_palette()

        self.setStyleSheet(
            "QWidget { background: #111820; color: #EAF0F6; }"
            "QLabel { color: #EAF0F6; }"
            "QComboBox, QLineEdit, QSpinBox, QListWidget {"
            "background: #1A2430;"
            "border: 1px solid #314355;"
            "border-radius: 10px;"
            "padding: 8px;"
            "color: #EAF0F6;"
            "}"
            "QPushButton {"
            "background: #E3A23B;"
            "border: none;"
            "border-radius: 10px;"
            "padding: 10px 14px;"
            "color: #1E1609;"
            "font-weight: 700;"
            "}"
            "QPushButton:hover { background: #F0B557; }"
            "QGroupBox {"
            "border: 1px solid #2A3A49;"
            "border-radius: 16px;"
            "margin-top: 10px;"
            "padding: 14px;"
            "background: #151F29;"
            "}"
            "QGroupBox::title {"
            "subcontrol-origin: margin;"
            "left: 12px;"
            "padding: 0 6px;"
            "color: #F3F6FA;"
            "font-weight: 700;"
            "}"
        )

    def _build_section_card(self, title: str) -> QGroupBox:
        card = QGroupBox(title)
        card.setFlat(False)
        return card

    def _build_spin_box(self, minimum: int, maximum: int) -> QSpinBox:
        spin_box = QSpinBox()
        spin_box.setRange(minimum, maximum)
        return spin_box

    def refresh(self) -> None:
        self._refresh_management_state()
        self._refresh_management_instances()
        self._refresh_definition_metadata()
        self._refresh_palette()

    def _notify_state_changed(self) -> None:
        if self._on_state_changed is not None:
            self._on_state_changed()

    def _refresh_management_state(self) -> None:
        self._management_state = self._management_controller.load_management_state()

    def _refresh_palette(self) -> None:
        if self._widget_palette is None:
            return
        selected_widget_id = None
        if self._management_widget_selector is not None:
            selected_widget_id = self._management_widget_selector.currentData()
        self._widget_palette.set_definitions(
            self._management_state.widget_definitions,
            selected_widget_id=selected_widget_id,
        )

    def _refresh_management_instances(self, *_args) -> None:
        if self._management_screen_selector is None or self._widget_instance_list is None:
            return

        self._refresh_management_state()
        self._widget_instance_list.clear()
        screen = self._current_screen()
        if screen is None:
            return

        self._apply_screen_state(screen)
        self._refresh_layout_preview(screen)
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
        self._notify_state_changed()
        self._refresh_layout_preview(self._current_screen())

    def _handle_palette_select(self, widget_id: str) -> None:
        if self._management_widget_selector is None:
            return
        for index in range(self._management_widget_selector.count()):
            if self._management_widget_selector.itemData(index) == widget_id:
                self._management_widget_selector.setCurrentIndex(index)
                self._refresh_palette()
                return

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
        self._notify_state_changed()
        self._refresh_layout_preview(self._current_screen())

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
            self._clear_launcher_settings()
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
        if instance is None:
            self._web_url_input.clear()
            self._web_mobile_checkbox.setChecked(False)
            self._clear_launcher_settings()
            self._refresh_instance_metadata(instance)
            return

        if instance.widget_id == "web":
            self._web_url_input.setText(str(instance.settings.get("url", "")))
            self._web_mobile_checkbox.setChecked(bool(instance.settings.get("force_mobile", False)))
        else:
            self._web_url_input.clear()
            self._web_mobile_checkbox.setChecked(False)

        if instance.widget_id == "launcher":
            self._load_launcher_settings(instance.settings.get("items"))
        else:
            self._clear_launcher_settings()

        self._refresh_instance_metadata(instance)
        self._refresh_layout_preview(screen)

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
        self._notify_state_changed()
        self._refresh_layout_preview(self._current_screen())

    def _handle_save_launcher_settings(self) -> None:
        if self._management_screen_selector is None or self._widget_instance_list is None:
            return

        current_item = self._widget_instance_list.currentItem()
        if current_item is None:
            return

        try:
            self._management_controller.configure_launcher_widget(
                screen_id=self._management_screen_selector.currentData(),
                instance_id=current_item.data(Qt.ItemDataRole.UserRole),
                items=[
                    {
                        "label": label_input.text(),
                        "target": target_input.text(),
                    }
                    for label_input, target_input in zip(
                        self._launcher_label_inputs,
                        self._launcher_target_inputs,
                    )
                ],
            )
        except ValueError as error:
            QMessageBox.warning(self, "Launcher configuration failed", str(error))
            return

        self.refresh()
        self._notify_state_changed()
        self._refresh_layout_preview(self._current_screen())

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

    def _selected_instance_id(self) -> str | None:
        if self._widget_instance_list is None:
            return None
        current_item = self._widget_instance_list.currentItem()
        if current_item is None:
            return None
        return current_item.data(Qt.ItemDataRole.UserRole)

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
            *self._launcher_label_inputs,
            *self._launcher_target_inputs,
            self._add_widget_button,
            self._suggest_placement_button,
            self._remove_widget_button,
            self._save_web_button,
            self._save_launcher_button,
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
            self._clear_launcher_settings()
            self._refresh_instance_metadata(None)

    def _load_launcher_settings(self, items) -> None:
        self._clear_launcher_settings()
        if not isinstance(items, list):
            return
        for index, item in enumerate(items[: len(self._launcher_label_inputs)]):
            if not isinstance(item, dict):
                continue
            self._launcher_label_inputs[index].setText(str(item.get("label", "")))
            self._launcher_target_inputs[index].setText(str(item.get("target", "")))

    def _clear_launcher_settings(self) -> None:
        for label_input, target_input in zip(
            self._launcher_label_inputs,
            self._launcher_target_inputs,
        ):
            label_input.clear()
            target_input.clear()

    def _refresh_layout_preview(self, screen: Screen | None) -> None:
        if self._layout_preview is None:
            return
        self._layout_preview.set_screen(
            screen=screen,
            definitions=self._management_state.widget_definitions,
            selected_instance_id=self._selected_instance_id(),
        )

    def _handle_preview_select(self, instance_id: str) -> None:
        if self._widget_instance_list is None:
            return
        for index in range(self._widget_instance_list.count()):
            item = self._widget_instance_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == instance_id:
                self._widget_instance_list.setCurrentItem(item)
                return

    def _handle_preview_move(self, instance_id: str, column: int, row: int) -> None:
        screen = self._current_screen()
        if screen is None:
            return
        instance = next(
            (item for item in screen.layout.widget_instances if item.instance_id == instance_id),
            None,
        )
        if instance is None:
            return
        try:
            self._management_controller.update_widget_instance_placement(
                screen_id=screen.screen_id,
                instance_id=instance_id,
                column=column,
                row=row,
                width=instance.placement.width,
                height=instance.placement.height,
            )
        except ValueError as error:
            QMessageBox.warning(self, "Move rejected", str(error))
            self._refresh_layout_preview(screen)
            return
        self.refresh()
        self._notify_state_changed()
        self._handle_preview_select(instance_id)

    def _handle_preview_resize(self, instance_id: str, size_preset: str) -> None:
        screen = self._current_screen()
        if screen is None:
            return
        instance = next(
            (item for item in screen.layout.widget_instances if item.instance_id == instance_id),
            None,
        )
        if instance is None:
            return
        _, width, height = WidgetSize.from_preset(size_preset)
        try:
            self._management_controller.update_widget_instance_placement(
                screen_id=screen.screen_id,
                instance_id=instance_id,
                column=instance.placement.column,
                row=instance.placement.row,
                width=width,
                height=height,
            )
        except ValueError as error:
            QMessageBox.warning(self, "Resize rejected", str(error))
            self._refresh_layout_preview(screen)
            return
        self.refresh()
        self._notify_state_changed()
        self._handle_preview_select(instance_id)

    def _handle_preview_add(self, widget_id: str, column: int, row: int) -> None:
        if self._management_screen_selector is None:
            return
        try:
            self._management_controller.add_widget_instance_from_preset(
                screen_id=self._management_screen_selector.currentData(),
                widget_id=widget_id,
                column=column,
                row=row,
                size_preset="1/6",
            )
        except ValueError as error:
            QMessageBox.warning(self, "Add rejected", str(error))
            self._refresh_layout_preview(self._current_screen())
            return
        self._handle_palette_select(widget_id)
        self.refresh()
        self._notify_state_changed()

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
