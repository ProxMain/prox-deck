from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from proxdeck.application.controllers.management_controller import ManagementController
from proxdeck.domain.models.screen import Screen
from proxdeck.presentation.views.layout_preview import LayoutPreviewWidget
from proxdeck.presentation.views.scene_svg import build_svg_label
from proxdeck.presentation.views.widget_definition_summary import format_widget_definition_summary
from proxdeck.presentation.views.widget_palette import WidgetPaletteView
from proxdeck.presentation.widgets.widget_host_factory import WidgetHostFactory

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QFormLayout,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError:  # pragma: no cover
    Qt = None
    QCheckBox = object
    QComboBox = object
    QFormLayout = object
    QFrame = object
    QGroupBox = object
    QHBoxLayout = object
    QLabel = object
    QLineEdit = object
    QListWidget = object
    QListWidgetItem = object
    QMessageBox = object
    QPushButton = object
    QScrollArea = object
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
        self._selected_palette_widget_id: str | None = None
        self._management_screen_selector: QComboBox | None = None
        self._management_widget_selector: QComboBox | None = None
        self._widget_palette: WidgetPaletteView | None = None
        self._widget_instance_list: QListWidget | None = None
        self._layout_preview: LayoutPreviewWidget | None = None
        self._management_status_label: QLabel | None = None
        self._definition_metadata_label: QLabel | None = None
        self._instance_metadata_label: QLabel | None = None
        self._inspector_title_label: QLabel | None = None
        self._inspector_subtitle_label: QLabel | None = None
        self._web_card: QGroupBox | None = None
        self._web_url_input: QLineEdit | None = None
        self._web_mobile_checkbox: QCheckBox | None = None
        self._save_web_button: QPushButton | None = None
        self._launcher_card: QGroupBox | None = None
        self._launcher_label_inputs: list[QLineEdit] = []
        self._launcher_target_inputs: list[QLineEdit] = []
        self._save_launcher_button: QPushButton | None = None
        self._remove_widget_button: QPushButton | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("HeroPanel")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(22, 20, 22, 20)
        hero_stack = QVBoxLayout()
        hero_stack.setSpacing(6)
        kicker = QLabel("PROX DECK // CONTROL ROOM")
        kicker.setObjectName("HeroKicker")
        hero_stack.addWidget(kicker)
        title = QLabel("Build The Deck Like A Mission")
        title.setObjectName("HeroTitle")
        hero_stack.addWidget(title)
        subtitle = QLabel("Deploy widgets onto the Xeneon Edge with a visual staging bay, not a settings form.")
        subtitle.setObjectName("HeroSubtitle")
        subtitle.setWordWrap(True)
        hero_stack.addWidget(subtitle)
        hero_layout.addLayout(hero_stack, 1)
        hero_layout.addWidget(build_svg_label("command_ring.svg", 128, 128), 0, Qt.AlignmentFlag.AlignCenter)
        self._management_status_label = QLabel()
        self._management_status_label.setObjectName("StatusChip")
        self._management_status_label.setWordWrap(True)
        self._management_status_label.setMinimumWidth(260)
        hero_layout.addWidget(self._management_status_label, 0, Qt.AlignmentFlag.AlignTop)
        root.addWidget(hero)

        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, 1)

        self._build_left_panel(body)
        self._build_stage_panel(body)
        self._build_inspector_panel(body)
        self._apply_theme()
        self._refresh_management_instances()
        self._refresh_definition_metadata()
        self._refresh_palette()

    def _build_left_panel(self, body: QHBoxLayout) -> None:
        panel = QFrame()
        panel.setObjectName("RailPanel")
        panel.setMaximumWidth(360)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        section_title = QLabel("Arsenal")
        section_title.setObjectName("SectionTitle")
        header = QHBoxLayout()
        header.addWidget(section_title)
        header.addStretch(1)
        header.addWidget(build_svg_label("arsenal_emblem.svg", 44, 44))
        layout.addLayout(header)
        section_caption = QLabel("Choose the active screen and arm the next widget.")
        section_caption.setObjectName("SectionCaption")
        section_caption.setWordWrap(True)
        layout.addWidget(section_caption)

        screen_card = self._signal_card()
        screen_layout = QVBoxLayout(screen_card)
        screen_layout.addWidget(self._caption_label("Deployment Target"))
        self._management_screen_selector = QComboBox()
        for screen in self._management_state.screens:
            label = screen.name if screen.is_available() else f"{screen.name} (Soon)"
            self._management_screen_selector.addItem(label, screen.screen_id)
        self._management_screen_selector.currentIndexChanged.connect(self._refresh_management_instances)
        screen_layout.addWidget(self._management_screen_selector)
        layout.addWidget(screen_card)

        palette_card = self._signal_card()
        palette_layout = QVBoxLayout(palette_card)
        palette_title = QLabel("Widget Loadout")
        palette_title.setObjectName("SectionTitle")
        palette_layout.addWidget(palette_title)
        self._management_widget_selector = QComboBox()
        for definition in self._management_state.widget_definitions:
            self._management_widget_selector.addItem(definition.display_name, definition.widget_id)
        self._management_widget_selector.currentIndexChanged.connect(self._refresh_definition_metadata)
        self._management_widget_selector.hide()
        palette_layout.addWidget(self._management_widget_selector)
        self._widget_palette = WidgetPaletteView(on_select_widget=self._handle_palette_select)
        palette_layout.addWidget(self._widget_palette)
        self._definition_metadata_label = QLabel()
        self._definition_metadata_label.setObjectName("PanelText")
        self._definition_metadata_label.setWordWrap(True)
        palette_layout.addWidget(self._definition_metadata_label)
        layout.addWidget(palette_card, 1)
        body.addWidget(panel, 1)

    def _build_stage_panel(self, body: QHBoxLayout) -> None:
        panel = QFrame()
        panel.setObjectName("StagePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        title = QLabel("Deployment Stage")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)
        caption = QLabel("Select, place, resize, and pull widgets into formation.")
        caption.setObjectName("SectionCaption")
        caption.setWordWrap(True)
        layout.addWidget(caption)
        self._layout_preview = LayoutPreviewWidget(
            on_move_instance=self._handle_preview_move,
            on_resize_instance=self._handle_preview_resize,
            on_remove_instance=self._handle_preview_remove,
            on_select_instance=self._handle_preview_select,
            on_add_widget=self._handle_preview_add,
            on_activate_cell=self._handle_preview_cell_activate,
            render_widget_preview=lambda instance, definition: self._widget_host_factory.create_widget(
                instance,
                definition,
                live_updates=False,
            ),
        )
        self._layout_preview.setMinimumHeight(620)
        layout.addWidget(self._layout_preview, 1)
        self._widget_instance_list = QListWidget()
        self._widget_instance_list.currentItemChanged.connect(self._load_web_widget_settings)
        self._widget_instance_list.hide()
        layout.addWidget(self._widget_instance_list)
        self._remove_widget_button = QPushButton("Remove Selected")
        self._remove_widget_button.clicked.connect(self._handle_remove_widget)
        self._remove_widget_button.hide()
        layout.addWidget(self._remove_widget_button)
        body.addWidget(panel, 2)

    def _build_inspector_panel(self, body: QHBoxLayout) -> None:
        panel = QFrame()
        panel.setObjectName("InspectorPanel")
        panel.setMaximumWidth(380)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(14)
        title = QLabel("Inspector")
        title.setObjectName("SectionTitle")
        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(build_svg_label("inspector_emblem.svg", 44, 44))
        outer.addLayout(header)
        caption = QLabel("Only the selected widget exposes its live controls.")
        caption.setObjectName("SectionCaption")
        caption.setWordWrap(True)
        outer.addWidget(caption)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll, 1)
        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        identity = self._signal_card()
        identity_layout = QVBoxLayout(identity)
        self._inspector_subtitle_label = QLabel("NO ACTIVE WIDGET")
        self._inspector_subtitle_label.setObjectName("InspectorSubTitle")
        identity_layout.addWidget(self._inspector_subtitle_label)
        self._inspector_title_label = QLabel("Select a tile on the stage")
        self._inspector_title_label.setObjectName("InspectorTitle")
        self._inspector_title_label.setWordWrap(True)
        identity_layout.addWidget(self._inspector_title_label)
        self._instance_metadata_label = QLabel("Choose a widget from the arsenal, or click a deployed tile to inspect it.")
        self._instance_metadata_label.setObjectName("PanelText")
        self._instance_metadata_label.setWordWrap(True)
        identity_layout.addWidget(self._instance_metadata_label)
        layout.addWidget(identity)
        self._build_web_card(layout)
        self._build_launcher_card(layout)
        layout.addStretch(1)
        body.addWidget(panel, 1)

    def _build_web_card(self, layout: QVBoxLayout) -> None:
        self._web_card = QGroupBox("Browser Signal")
        web = QVBoxLayout(self._web_card)
        hint = QLabel("The web widget renders as a full-bleed Chromium surface inside its assigned slot.")
        hint.setObjectName("PanelText")
        hint.setWordWrap(True)
        web.addWidget(hint)
        self._web_url_input = QLineEdit()
        self._web_url_input.setPlaceholderText("https://example.com")
        web.addWidget(self._web_url_input)
        self._web_mobile_checkbox = QCheckBox("Mobile viewport")
        web.addWidget(self._web_mobile_checkbox)
        self._save_web_button = QPushButton("Apply Browser Route")
        self._save_web_button.clicked.connect(self._handle_save_web_settings)
        web.addWidget(self._save_web_button)
        layout.addWidget(self._web_card)

    def _build_launcher_card(self, layout: QVBoxLayout) -> None:
        self._launcher_card = QGroupBox("Launcher Loadout")
        launcher = QVBoxLayout(self._launcher_card)
        hint = QLabel("Tune quick actions for the selected launcher tile.")
        hint.setObjectName("PanelText")
        hint.setWordWrap(True)
        launcher.addWidget(hint)
        form = QFormLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        for index in range(4):
            label_input = QLineEdit()
            label_input.setPlaceholderText(f"Action {index + 1} label")
            target_input = QLineEdit()
            target_input.setPlaceholderText(f"Action {index + 1} target")
            self._launcher_label_inputs.append(label_input)
            self._launcher_target_inputs.append(target_input)
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            row_layout.addWidget(label_input, 1)
            row_layout.addWidget(target_input, 2)
            form.addRow(f"Slot {index + 1}", row)
        launcher.addLayout(form)
        self._save_launcher_button = QPushButton("Commit Loadout")
        self._save_launcher_button.clicked.connect(self._handle_save_launcher_settings)
        launcher.addWidget(self._save_launcher_button)
        layout.addWidget(self._launcher_card)
        self._sync_inspector_visibility(None)

    def _signal_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("SignalCard")
        return card

    def _caption_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionCaption")
        return label

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            "QWidget {background:#081018;color:#EAF1F9;font-family:'Segoe UI';}"
            "QFrame#HeroPanel {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #131E2A,stop:0.45 #0D151F,stop:1 #091017);border:1px solid #223648;border-radius:26px;}"
            "QFrame#RailPanel,QFrame#StagePanel,QFrame#InspectorPanel {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #101925,stop:1 #0B131B);border:1px solid #1E3142;border-radius:24px;}"
            "QFrame#SignalCard {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #172331,stop:1 #0F1822);border:1px solid #284054;border-radius:18px;}"
            "QLabel#HeroKicker {font-size:11px;font-weight:800;letter-spacing:1px;color:#F0B557;}"
            "QLabel#HeroTitle {font-size:34px;font-weight:900;color:#F4F8FC;}"
            "QLabel#HeroSubtitle,QLabel#SectionCaption,QLabel#PanelText {color:#8EA4B6;}"
            "QLabel#SectionTitle {font-size:15px;font-weight:800;color:#F4F8FC;}"
            "QLabel#InspectorTitle {font-size:20px;font-weight:900;color:#F4F8FC;}"
            "QLabel#InspectorSubTitle {font-size:12px;font-weight:700;color:#F0B557;}"
            "QLabel#StatusChip {background:#132130;border:1px solid #284054;border-radius:14px;padding:8px 12px;color:#DCE6F0;font-weight:700;}"
            "QComboBox,QLineEdit,QListWidget {background:#111C27;border:1px solid #2B4155;border-radius:14px;padding:10px 12px;color:#EFF5FB;selection-background-color:#F0B557;selection-color:#11171F;}"
            "QPushButton {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #F0B557,stop:1 #E48D3A);border:none;border-radius:14px;padding:11px 14px;color:#16110B;font-size:12px;font-weight:800;}"
            "QPushButton:hover {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #F6C36F,stop:1 #EEA252);}"
            "QCheckBox {font-weight:700;color:#D9E4EE;}"
            "QCheckBox::indicator {width:20px;height:20px;border-radius:6px;border:1px solid #345069;background:#101923;}"
            "QCheckBox::indicator:checked {background:#F0B557;border:1px solid #F0B557;}"
            "QGroupBox {border:1px solid #25384A;border-radius:20px;margin-top:12px;padding:14px;background:#0E1720;}"
            "QGroupBox::title {subcontrol-origin:margin;left:14px;padding:0 6px;font-size:13px;font-weight:800;color:#F3F7FB;}"
        )

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
        selected_widget_id = self._selected_palette_widget_id
        if selected_widget_id is None and self._management_widget_selector is not None:
            selected_widget_id = self._management_widget_selector.currentData()
        self._widget_palette.set_definitions(
            self._management_state.widget_definitions,
            selected_widget_id=selected_widget_id,
        )

    def _refresh_management_instances(self, *_args) -> None:
        if self._management_screen_selector is None or self._widget_instance_list is None:
            return
        selected_instance_id = self._selected_instance_id()
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
        if selected_instance_id is not None:
            self._handle_preview_select(selected_instance_id)
        elif self._widget_instance_list.count() > 0:
            self._widget_instance_list.setCurrentRow(0)
        else:
            self._refresh_instance_metadata(None)

    def _handle_palette_select(self, widget_id: str) -> None:
        self._selected_palette_widget_id = widget_id
        if self._management_widget_selector is None:
            return
        for index in range(self._management_widget_selector.count()):
            if self._management_widget_selector.itemData(index) == widget_id:
                self._management_widget_selector.setCurrentIndex(index)
                self._refresh_palette()
                if self._management_status_label is not None:
                    self._management_status_label.setText(
                        f"{self._management_widget_selector.currentText()} ready. Click a slot to place it."
                    )
                return

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
            self._refresh_instance_metadata(None)
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
                    {"label": label_input.text(), "target": target_input.text()}
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

    def _refresh_definition_metadata(self, *_args) -> None:
        if self._management_widget_selector is None or self._definition_metadata_label is None:
            return
        definition = self._find_widget_definition(self._management_widget_selector.currentData())
        if definition is None:
            self._definition_metadata_label.setText("No widget armed.")
            return
        self._definition_metadata_label.setText(format_widget_definition_summary(definition))

    def _refresh_instance_metadata(self, instance) -> None:
        if (
            self._instance_metadata_label is None
            or self._inspector_title_label is None
            or self._inspector_subtitle_label is None
        ):
            return
        if instance is None:
            self._inspector_subtitle_label.setText("NO ACTIVE WIDGET")
            self._inspector_title_label.setText("Select a tile on the stage")
            self._instance_metadata_label.setText(
                "Choose a widget from the arsenal, or click a deployed tile to inspect it."
            )
            self._sync_inspector_visibility(None)
            return
        definition = self._find_widget_definition(instance.widget_id)
        if definition is None:
            self._inspector_subtitle_label.setText(instance.instance_id.upper())
            self._inspector_title_label.setText(instance.widget_id)
            self._instance_metadata_label.setText("Manifest metadata unavailable for this deployed widget.")
            self._sync_inspector_visibility(instance)
            return
        self._inspector_subtitle_label.setText(instance.instance_id.upper())
        self._inspector_title_label.setText(definition.display_name)
        self._instance_metadata_label.setText(
            f"Widget ID: {definition.widget_id}\n"
            f"Entrypoint: {definition.entrypoint}\n"
            f"Distribution: {definition.install_metadata.distribution}\n"
            f"Scope: {definition.install_metadata.installation_scope}"
        )
        self._sync_inspector_visibility(instance)

    def _sync_inspector_visibility(self, instance) -> None:
        widget_id = None if instance is None else instance.widget_id
        if self._web_card is not None:
            self._web_card.setVisible(widget_id == "web")
        if self._launcher_card is not None:
            self._launcher_card.setVisible(widget_id == "launcher")

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
            self._widget_palette,
            self._layout_preview,
            self._widget_instance_list,
            self._web_url_input,
            self._web_mobile_checkbox,
            *self._launcher_label_inputs,
            *self._launcher_target_inputs,
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
        self._selected_palette_widget_id = None
        self._refresh_palette()
        if self._widget_instance_list is None:
            return
        for index in range(self._widget_instance_list.count()):
            item = self._widget_instance_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == instance_id:
                self._widget_instance_list.setCurrentItem(item)
                if self._management_status_label is not None:
                    self._management_status_label.setText("Widget selected. Click a slot to move it.")
                return

    def _handle_preview_cell_activate(self, column: int, row: int) -> None:
        if self._management_screen_selector is None:
            return
        if self._selected_palette_widget_id is not None:
            self._handle_preview_add(self._selected_palette_widget_id, column, row)
            self._selected_palette_widget_id = None
            self._refresh_palette()
            return
        instance_id = self._selected_instance_id()
        if instance_id is not None:
            self._handle_preview_move(instance_id, column, row)
            return
        if self._management_status_label is not None:
            self._management_status_label.setText("Choose a widget first.")

    def _handle_preview_move(self, instance_id: str, column: int, row: int) -> None:
        screen = self._current_screen()
        if screen is None:
            return
        try:
            self._management_controller.move_widget_instance_smart(
                screen_id=screen.screen_id,
                instance_id=instance_id,
                preferred_column=column,
                preferred_row=row,
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
        try:
            self._management_controller.resize_widget_instance_smart(
                screen_id=screen.screen_id,
                instance_id=instance_id,
                size_preset=size_preset,
            )
        except ValueError as error:
            QMessageBox.warning(self, "Resize rejected", str(error))
            self._refresh_layout_preview(screen)
            return
        self.refresh()
        self._notify_state_changed()
        self._handle_preview_select(instance_id)

    def _handle_preview_remove(self, instance_id: str) -> None:
        if self._management_screen_selector is None:
            return
        try:
            self._management_controller.remove_widget_instance(
                screen_id=self._management_screen_selector.currentData(),
                instance_id=instance_id,
            )
        except ValueError as error:
            QMessageBox.warning(self, "Remove rejected", str(error))
            self._refresh_layout_preview(self._current_screen())
            return
        self.refresh()
        self._notify_state_changed()

    def _handle_preview_add(self, widget_id: str, column: int, row: int) -> None:
        if self._management_screen_selector is None:
            return
        try:
            updated_screen = self._management_controller.add_widget_instance_smart(
                screen_id=self._management_screen_selector.currentData(),
                widget_id=widget_id,
                preferred_column=column,
                preferred_row=row,
                size_preset="1/6",
            )
        except ValueError as error:
            QMessageBox.warning(self, "Add rejected", str(error))
            self._refresh_layout_preview(self._current_screen())
            return
        self._handle_palette_select(widget_id)
        self._selected_palette_widget_id = None
        self._refresh_palette()
        self.refresh()
        self._notify_state_changed()
        if updated_screen.layout.widget_instances:
            self._handle_preview_select(updated_screen.layout.widget_instances[-1].instance_id)

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
