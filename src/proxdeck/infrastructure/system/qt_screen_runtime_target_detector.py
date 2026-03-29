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
    DEFAULT_TARGET_NAME_HINTS = (
        "corsair xeneon edge",
        "xeneon edge",
        "xeneon",
    )

    def __init__(
        self,
        screen_provider: Callable[[], list[ScreenSnapshot]] | None = None,
    ) -> None:
        self._screen_provider = screen_provider or self._read_qt_screens

    def detect_target(self) -> RuntimeTarget | None:
        override = self._read_override_target()
        if override is not None:
            return override

        screens = self._screen_provider()
        named_target = self._find_named_target(screens)
        if named_target is not None:
            return named_target

        target_width = int(os.getenv("PROXDECK_TARGET_WIDTH", str(self.TARGET_WIDTH)))
        target_height = int(os.getenv("PROXDECK_TARGET_HEIGHT", str(self.TARGET_HEIGHT)))
        for screen in screens:
            if screen.width == target_width and screen.height == target_height:
                return self._build_runtime_target(screen)
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

    def _find_named_target(self, screens: list[ScreenSnapshot]) -> RuntimeTarget | None:
        for name_hint in self._read_target_name_hints():
            lowered_hint = name_hint.lower()
            for screen in screens:
                if lowered_hint in screen.name.lower():
                    return self._build_runtime_target(screen)
        return None

    def _read_target_name_hints(self) -> tuple[str, ...]:
        configured_hints = os.getenv("PROXDECK_TARGET_MONITOR_NAMES")
        if configured_hints:
            hints = tuple(
                hint.strip()
                for hint in configured_hints.split(",")
                if hint.strip()
            )
            if hints:
                return hints
        return self.DEFAULT_TARGET_NAME_HINTS

    @staticmethod
    def _build_runtime_target(screen: ScreenSnapshot) -> RuntimeTarget:
        return RuntimeTarget(
            monitor_name=screen.name,
            width=screen.width,
            height=screen.height,
            x=screen.x,
            y=screen.y,
        )
