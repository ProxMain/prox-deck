from __future__ import annotations

from collections.abc import Callable

from proxdeck.domain.models.widget_definition import WidgetDefinition

try:
    from PySide6.QtCore import QMimeData, QPoint, Qt
    from PySide6.QtGui import QDrag, QMouseEvent
    from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QMimeData = object
    QPoint = object
    Qt = object
    QDrag = object
    QMouseEvent = object
    QFrame = object
    QGridLayout = object
    QLabel = object
    QVBoxLayout = object
    QWidget = object


class WidgetPaletteView(QFrame):
    def __init__(self, on_select_widget: Callable[[str], None]) -> None:
        super().__init__()
        self._on_select_widget = on_select_widget
        self._selected_widget_id: str | None = None
        self._definitions: tuple[WidgetDefinition, ...] = tuple()
        self._grid_layout = QGridLayout(self)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(10)

    def set_definitions(
        self,
        definitions: tuple[WidgetDefinition, ...],
        selected_widget_id: str | None,
    ) -> None:
        self._definitions = definitions
        self._selected_widget_id = selected_widget_id
        self._rebuild()

    def _rebuild(self) -> None:
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for index, definition in enumerate(self._definitions):
            card = _PaletteCard(
                definition=definition,
                selected=definition.widget_id == self._selected_widget_id,
                on_select=self._on_select_widget,
                parent=self,
            )
            self._grid_layout.addWidget(card, index // 2, index % 2)


class _PaletteCard(QFrame):
    def __init__(
        self,
        definition: WidgetDefinition,
        selected: bool,
        on_select: Callable[[str], None],
        parent: QWidget,
    ) -> None:
        super().__init__(parent)
        self._definition = definition
        self._on_select = on_select
        self._drag_start: QPoint | None = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setStyleSheet(
            "QFrame {"
            f"background: {'#2A3F53' if selected else '#18232D'};"
            f"border: 2px solid {'#8BD3FF' if selected else '#314355'};"
            "border-radius: 14px;"
            "}"
            "QLabel { background: transparent; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        title = QLabel(definition.display_name)
        title.setStyleSheet("font-size: 14px; font-weight: 700; color: #EAF0F6;")
        layout.addWidget(title)

        kind = QLabel(definition.kind.value.title())
        kind.setStyleSheet("font-size: 11px; color: #8FA3B7;")
        layout.addWidget(kind)

        capabilities = ", ".join(sorted(definition.capabilities.values)) or "none"
        detail = QLabel(f"Capabilities: {capabilities}")
        detail.setWordWrap(True)
        detail.setStyleSheet("font-size: 11px; color: #B8C7D5;")
        layout.addWidget(detail)

        hint = QLabel("Drag into the grid")
        hint.setStyleSheet("font-size: 11px; color: #E3A23B; font-weight: 700;")
        layout.addWidget(hint)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        self._on_select(self._definition.widget_id)
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
        mime_data.setData("application/x-proxdeck-widget", self._definition.widget_id.encode("utf-8"))
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction)
        self._drag_start = None
        super().mouseMoveEvent(event)
