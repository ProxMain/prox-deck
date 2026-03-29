from __future__ import annotations

from collections.abc import Callable

from proxdeck.domain.models.screen import Screen
from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance

try:
    from PySide6.QtCore import QMimeData, QPoint, Qt
    from PySide6.QtGui import QDrag, QMouseEvent
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QMimeData = object
    QPoint = object
    Qt = object
    QDrag = object
    QMouseEvent = object
    QFrame = object
    QHBoxLayout = object
    QLabel = object
    QPushButton = object
    QVBoxLayout = object
    QWidget = object


class LayoutPreviewWidget(QFrame):
    def __init__(
        self,
        on_move_instance: Callable[[str, int, int], None],
        on_resize_instance: Callable[[str, str], None],
        on_select_instance: Callable[[str], None],
        on_add_widget: Callable[[str, int, int], None],
        render_widget_preview: Callable[[WidgetInstance, WidgetDefinition | None], QWidget],
    ) -> None:
        super().__init__()
        self._on_move_instance = on_move_instance
        self._on_resize_instance = on_resize_instance
        self._on_select_instance = on_select_instance
        self._on_add_widget = on_add_widget
        self._render_widget_preview = render_widget_preview
        self._screen: Screen | None = None
        self._definitions: dict[str, WidgetDefinition] = {}
        self._selected_instance_id: str | None = None
        self.setAcceptDrops(True)
        self.setMinimumHeight(320)
        self.setStyleSheet(
            "QFrame {"
            "background: #101821;"
            "border: 1px solid #314355;"
            "border-radius: 16px;"
            "}"
        )

    def set_screen(
        self,
        screen: Screen | None,
        definitions: tuple[WidgetDefinition, ...],
        selected_instance_id: str | None,
    ) -> None:
        self._screen = screen
        self._definitions = {definition.widget_id: definition for definition in definitions}
        self._selected_instance_id = selected_instance_id
        self._rebuild()

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if (
            event.mimeData().hasFormat("application/x-proxdeck-instance")
            or event.mimeData().hasFormat("application/x-proxdeck-widget")
        ):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        if self._screen is None:
            event.ignore()
            return

        cell = self._cell_at_position(event.position().toPoint())
        if cell is None:
            event.ignore()
            return

        if event.mimeData().hasFormat("application/x-proxdeck-instance"):
            data = bytes(event.mimeData().data("application/x-proxdeck-instance")).decode("utf-8")
            self._on_move_instance(data, cell[0], cell[1])
        elif event.mimeData().hasFormat("application/x-proxdeck-widget"):
            data = bytes(event.mimeData().data("application/x-proxdeck-widget")).decode("utf-8")
            self._on_add_widget(data, cell[0], cell[1])
        else:
            event.ignore()
            return
        event.acceptProposedAction()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._rebuild()

    def _rebuild(self) -> None:
        for child in self.findChildren(_PreviewTile):
            child.deleteLater()
        for child in self.findChildren(QLabel, "preview-empty-cell"):
            child.deleteLater()

        if self._screen is None:
            return

        occupied = set()
        for instance in self._screen.layout.widget_instances:
            occupied.update(instance.placement.cells())
            tile = _PreviewTile(
                instance=instance,
                display_name=self._display_name_for(instance),
                preview_widget=self._render_widget_preview(
                    instance,
                    self._definitions.get(instance.widget_id),
                ),
                selected=instance.instance_id == self._selected_instance_id,
                on_resize=self._on_resize_instance,
                on_select=self._on_select_instance,
                parent=self,
            )
            x, y, width, height = self._geometry_for(instance)
            tile.setGeometry(x, y, width, height)
            tile.show()

        for row in range(2):
            for column in range(3):
                if (column, row) in occupied:
                    continue
                label = QLabel("Empty", self)
                label.setObjectName("preview-empty-cell")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                x, y, width, height = self._geometry_for_cell(column, row)
                label.setGeometry(x, y, width, height)
                label.setStyleSheet(
                    "QLabel {"
                    "color: #6F879B;"
                    "background: #16212C;"
                    "border: 1px dashed #415062;"
                    "border-radius: 12px;"
                    "}"
                )
                label.show()

    def _display_name_for(self, instance: WidgetInstance) -> str:
        definition = self._definitions.get(instance.widget_id)
        if definition is None:
            return instance.widget_id
        return definition.display_name

    def _geometry_for(self, instance: WidgetInstance):
        left, top, cell_width, cell_height = self._grid_metrics()
        return (
            left + instance.placement.column * cell_width,
            top + instance.placement.row * cell_height,
            instance.placement.width * cell_width - 8,
            instance.placement.height * cell_height - 8,
        )

    def _geometry_for_cell(self, column: int, row: int):
        left, top, cell_width, cell_height = self._grid_metrics()
        return (
            left + column * cell_width,
            top + row * cell_height,
            cell_width - 8,
            cell_height - 8,
        )

    def _grid_metrics(self) -> tuple[int, int, int, int]:
        usable_width = max(300, self.width() - 16)
        usable_height = max(220, self.height() - 16)
        cell_width = usable_width // 3
        cell_height = usable_height // 2
        return 8, 8, cell_width, cell_height

    def _cell_at_position(self, point) -> tuple[int, int] | None:
        _, _, cell_width, cell_height = self._grid_metrics()
        column = max(0, min(2, (point.x() - 8) // cell_width))
        row = max(0, min(1, (point.y() - 8) // cell_height))
        return int(column), int(row)


class _PreviewTile(QFrame):
    def __init__(
        self,
        instance: WidgetInstance,
        display_name: str,
        preview_widget: QWidget,
        selected: bool,
        on_resize: Callable[[str, str], None],
        on_select: Callable[[str], None],
        parent: QWidget,
    ) -> None:
        super().__init__(parent)
        self._instance = instance
        self._on_resize = on_resize
        self._on_select = on_select
        self._drag_start: QPoint | None = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setStyleSheet(
            "QFrame {"
            f"background: {'#294962' if selected else '#1E2C3A'};"
            f"border: 2px solid {'#8BD3FF' if selected else '#5A778F'};"
            "border-radius: 12px;"
            "}"
            "QLabel { color: #EAF0F6; background: transparent; }"
            "QPushButton {"
            "background: #E3A23B;"
            "border: none;"
            "border-radius: 8px;"
            "padding: 4px 8px;"
            "color: #1E1609;"
            "font-size: 11px;"
            "font-weight: 700;"
            "}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        label = QLabel(display_name)
        label.setWordWrap(True)
        header_layout.addWidget(label, 1)

        controls = QWidget(self)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(4)
        for text, preset in (
            ("1", "1/6"),
            ("2W", "2/6-wide"),
            ("2T", "2/6-tall"),
            ("4", "4/6"),
            ("6", "6/6"),
        ):
            button = QPushButton(text)
            button.clicked.connect(
                lambda _checked=False, selected_preset=preset: self._on_resize(
                    self._instance.instance_id,
                    selected_preset,
                )
            )
            controls_layout.addWidget(button)
        header_layout.addWidget(controls)
        layout.addWidget(header)

        preview_widget.setParent(self)
        _make_preview_non_interactive(preview_widget)
        layout.addWidget(preview_widget, 1)
        controls.hide()
        self._controls = controls

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self._controls.show()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self._controls.hide()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        self._on_select(self._instance.instance_id)
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if (
            self._drag_start is None
            or not (event.buttons() & Qt.MouseButton.LeftButton)
            or QDrag is object
            or QMimeData is object
        ):
            super().mouseMoveEvent(event)
            return

        if (event.position().toPoint() - self._drag_start).manhattanLength() < 10:
            super().mouseMoveEvent(event)
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData(
            "application/x-proxdeck-instance",
            self._instance.instance_id.encode("utf-8"),
        )
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.MoveAction)
        self._drag_start = None
        super().mouseMoveEvent(event)


def _make_preview_non_interactive(widget: QWidget) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    for child in widget.findChildren(QWidget):
        child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        child.setFocusPolicy(Qt.FocusPolicy.NoFocus)
