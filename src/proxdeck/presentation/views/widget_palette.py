from __future__ import annotations

from collections.abc import Callable

from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.presentation.views.scene_svg import build_svg_label, widget_icon_asset

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    Qt = object
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
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            "QFrame {"
            f"background: {'#213547' if selected else '#16222C'};"
            f"border: 2px solid {'#F0B557' if selected else '#314355'};"
            "border-radius: 18px;"
            "}"
            "QLabel { background: transparent; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        badge = QLabel("Ready" if selected else "Add")
        badge.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #102030; "
            f"background: {'#F0B557' if selected else '#8FA3B7'}; border-radius: 9px; padding: 3px 8px;"
        )
        badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignLeft)

        icon_label = build_svg_label(widget_icon_asset(definition.widget_id), 48, 48)
        icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignLeft)

        title = QLabel(definition.display_name)
        title.setStyleSheet("font-size: 15px; font-weight: 800; color: #F5F8FB;")
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(title)

        kind = QLabel(definition.kind.value.title())
        kind.setStyleSheet("font-size: 11px; color: #8FA3B7;")
        kind.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(kind)

        capabilities = ", ".join(sorted(definition.capabilities.values)) or "none"
        detail = QLabel(f"Capabilities: {capabilities}")
        detail.setWordWrap(True)
        detail.setStyleSheet("font-size: 11px; color: #B8C7D5;")
        detail.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(detail)

        hint = QLabel("Click, then place")
        hint.setStyleSheet("font-size: 11px; color: #F0B557; font-weight: 700;")
        hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(hint)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        self._on_select(self._definition.widget_id)
        super().mousePressEvent(event)
