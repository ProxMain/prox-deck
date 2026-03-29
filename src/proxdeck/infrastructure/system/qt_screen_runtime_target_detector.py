from __future__ import annotations

import os
from collections.abc import Callable

from proxdeck.domain.contracts.runtime_target_detector import RuntimeTargetDetector
from proxdeck.domain.models.runtime_target import RuntimeTarget
from proxdeck.infrastructure.system.screen_snapshot import ScreenSnapshot

try:
    from PySide6.QtGui import QGuiApplication
except ModuleNotFoundError:  # pragma: no cover - optional in headless tests
    QGuiApplication = None


class QtScreenRuntimeTargetDetector(RuntimeTargetDetector):
    TARGET_WIDTH = 1920
    TARGET_HEIGHT = 1080

    def __init__(
        self,
        screen_provider: Callable[[], list[ScreenSnapshot]] | None = None,
    ) -> None:
        self._screen_provider = screen_provider or self._read_qt_screens

    def detect_target(self) -> RuntimeTarget | None:
        override = self._read_override_target()
        if override is not None:
            return override

        target_width = int(os.getenv("PROXDECK_TARGET_WIDTH", str(self.TARGET_WIDTH)))
        target_height = int(os.getenv("PROXDECK_TARGET_HEIGHT", str(self.TARGET_HEIGHT)))
        for screen in self._screen_provider():
            if screen.width == target_width and screen.height == target_height:
                return RuntimeTarget(
                    monitor_name=screen.name,
                    width=screen.width,
                    height=screen.height,
                    x=screen.x,
                    y=screen.y,
                )
        return None

    def _read_override_target(self) -> RuntimeTarget | None:
        detected = os.getenv("PROXDECK_DETECTED_MONITOR")
        if not detected:
            return None

        width = int(os.getenv("PROXDECK_TARGET_WIDTH", str(self.TARGET_WIDTH)))
        height = int(os.getenv("PROXDECK_TARGET_HEIGHT", str(self.TARGET_HEIGHT)))
        return RuntimeTarget(
            monitor_name=detected,
            width=width,
            height=height,
            x=int(os.getenv("PROXDECK_TARGET_X", "0")),
            y=int(os.getenv("PROXDECK_TARGET_Y", "0")),
        )

    def _read_qt_screens(self) -> list[ScreenSnapshot]:
        if QGuiApplication is None:
            return []

        app = QGuiApplication.instance()
        if app is None:
            return []

        snapshots: list[ScreenSnapshot] = []
        for screen in app.screens():
            geometry = screen.geometry()
            snapshots.append(
                ScreenSnapshot(
                    name=screen.name(),
                    width=geometry.width(),
                    height=geometry.height(),
                    x=geometry.x(),
                    y=geometry.y(),
                )
            )
        return snapshots
