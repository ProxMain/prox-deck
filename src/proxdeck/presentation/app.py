from __future__ import annotations

from collections.abc import Callable

from proxdeck.application.controllers.management_controller import ManagementController
from proxdeck.application.controllers.runtime_controller import RuntimeController
from proxdeck.application.dto.runtime_state import RuntimeState
from proxdeck.presentation.views.configuration_window import ConfigurationWindow
from proxdeck.presentation.views.runtime_window import RuntimeWindow

try:
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QAction, QBrush, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
    from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QPointF = object
    Qt = object
    QAction = object
    QBrush = object
    QColor = object
    QIcon = object
    QPainter = object
    QPainterPath = object
    QPen = object
    QPixmap = object
    QApplication = object
    QMenu = object
    QSystemTrayIcon = object


class ProxDeckApplication:
    def __init__(
        self,
        runtime_controller: RuntimeController,
        management_controller: ManagementController,
    ) -> None:
        self._runtime_controller = runtime_controller
        self._management_controller = management_controller
        self._runtime_window: RuntimeWindow | None = None
        self._configuration_window: ConfigurationWindow | None = None
        self._tray_icon: QSystemTrayIcon | None = None
        self._tray_menu: QMenu | None = None
        self._screen_menu: QMenu | None = None

    def start(self) -> RuntimeWindow:
        runtime_state = self._runtime_controller.load_runtime_state()
        self._runtime_window = RuntimeWindow(
            management_controller=self._management_controller,
            runtime_controller=self._runtime_controller,
            runtime_state=runtime_state,
        )
        self._runtime_window.show()
        self._configuration_window = ConfigurationWindow(
            management_controller=self._management_controller,
            on_state_changed=self.refresh_runtime,
        )
        self._build_tray_icon()
        return self._runtime_window

    def refresh_runtime(self) -> None:
        if self._runtime_window is None:
            return

        runtime_state = self._runtime_controller.load_runtime_state()
        self._runtime_window.reload_runtime_state(runtime_state)
        self._rebuild_tray_screen_menu(runtime_state)

    def show_configuration(self) -> None:
        if self._configuration_window is None:
            return

        self._configuration_window.show()
        self._configuration_window.raise_()
        self._configuration_window.activateWindow()

    def show_runtime(self) -> None:
        if self._runtime_window is None:
            return

        self._runtime_window.show()
        self._runtime_window.raise_()
        self._runtime_window.activateWindow()

    def switch_runtime_screen(self, screen_id: str) -> None:
        self._runtime_controller.switch_screen(screen_id)
        self.refresh_runtime()

    def _build_tray_icon(self) -> None:
        if QSystemTrayIcon is object or QApplication is object:
            return
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        runtime_state = self._runtime_controller.load_runtime_state()
        tray_menu = QMenu()
        self._tray_menu = tray_menu
        self._add_tray_action(tray_menu, "Open Configuration", self.show_configuration)
        self._add_tray_action(tray_menu, "Show Runtime", self.show_runtime)
        self._screen_menu = tray_menu.addMenu("Switch Screen")
        self._rebuild_tray_screen_menu(runtime_state)
        tray_menu.addSeparator()
        self._add_tray_action(tray_menu, "Quit", QApplication.quit)

        self._tray_icon = QSystemTrayIcon(self._build_tray_icon_asset())
        self._tray_icon.setToolTip("Prox Deck")
        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.activated.connect(self._handle_tray_activation)
        self._tray_icon.show()

    def _rebuild_tray_screen_menu(self, runtime_state: RuntimeState) -> None:
        if self._screen_menu is None:
            return

        self._screen_menu.clear()
        for entry in self._build_screen_menu_entries(runtime_state):
            action = self._screen_menu.addAction(entry["label"])
            action.setEnabled(entry["enabled"])
            action.setCheckable(True)
            action.setChecked(entry["checked"])
            if entry["enabled"]:
                action.triggered.connect(
                    lambda _checked=False, screen_id=entry["screen_id"]: self.switch_runtime_screen(
                        screen_id
                    )
                )

    def _handle_tray_activation(self, reason) -> None:
        if QSystemTrayIcon is object:
            return
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_configuration()

    @staticmethod
    def _build_screen_menu_entries(runtime_state: RuntimeState) -> list[dict[str, object]]:
        entries: list[dict[str, object]] = []
        for screen in runtime_state.available_screens:
            entries.append(
                {
                    "screen_id": screen.screen_id,
                    "label": screen.name if screen.is_available() else f"{screen.name} (Soon)",
                    "enabled": screen.is_available(),
                    "checked": screen.screen_id == runtime_state.active_screen.screen_id,
                }
            )
        return entries

    @staticmethod
    def _add_tray_action(menu: QMenu, text: str, callback: Callable[[], None]) -> QAction:
        action = menu.addAction(text)
        action.triggered.connect(callback)
        return action

    @staticmethod
    def _build_tray_icon_asset():
        if QPixmap is object or QPainter is object:
            return QIcon()
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#8C1111"))
        painter.drawRoundedRect(4, 4, 56, 56, 16, 16)

        painter.setBrush(QColor("#F6B21A"))
        painter.drawRoundedRect(10, 10, 44, 18, 9, 9)

        painter.setBrush(QColor("#D02A1A"))
        painter.drawRoundedRect(10, 32, 44, 22, 10, 10)

        painter.setPen(QPen(QColor("#FFF4D0"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(19, 43, 45, 43)

        painter.setPen(QPen(QColor("#FFF4D0"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        path = QPainterPath(QPointF(24, 20))
        path.lineTo(32, 14)
        path.lineTo(40, 20)
        painter.drawPath(path)

        painter.end()
        return QIcon(pixmap)
