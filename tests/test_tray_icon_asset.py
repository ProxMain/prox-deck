import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from proxdeck.presentation.app import ProxDeckApplication


def test_tray_icon_asset_is_custom_and_non_empty() -> None:
    app = QApplication.instance() or QApplication([])

    icon = ProxDeckApplication._build_tray_icon_asset()
    pixmap = icon.pixmap(64, 64)

    assert icon.isNull() is False
    assert pixmap.isNull() is False

    image = pixmap.toImage()
    top_color = image.pixelColor(20, 18).name().lower()
    bottom_color = image.pixelColor(14, 50).name().lower()

    assert top_color == "#f6b21a"
    assert bottom_color == "#d02a1a"
