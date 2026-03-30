from __future__ import annotations

from pathlib import Path

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QLabel
except ModuleNotFoundError:  # pragma: no cover
    Qt = None
    QPixmap = object
    QPainter = object
    QSvgRenderer = object
    QLabel = object


def build_svg_label(asset_name: str, width: int, height: int) -> QLabel:
    if QLabel is object or Qt is None:
        raise RuntimeError("PySide6 is required to build SVG labels")
    label = QLabel()
    label.setFixedSize(width, height)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    asset_path = Path(__file__).resolve().parent.parent / "assets" / asset_name

    if QSvgRenderer is object or not asset_path.exists():
        label.setText("")
        return label

    renderer = QSvgRenderer(str(asset_path))
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    label.setPixmap(pixmap)
    return label


def widget_icon_asset(widget_id: str) -> str:
    return {
        "clock": "icon_clock.svg",
        "web": "icon_web.svg",
        "launcher": "icon_launcher.svg",
        "stream-deck": "icon_stream_deck.svg",
        "notes": "icon_notes.svg",
        "system-stats": "icon_system.svg",
        "media-controls": "icon_media.svg",
    }.get(widget_id, "icon_generic.svg")
