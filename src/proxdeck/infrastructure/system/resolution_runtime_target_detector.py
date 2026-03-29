from __future__ import annotations

import os

from proxdeck.domain.contracts.runtime_target_detector import RuntimeTargetDetector
from proxdeck.domain.models.runtime_target import RuntimeTarget


class ResolutionRuntimeTargetDetector(RuntimeTargetDetector):
    """Detect the Edge target using explicit environment overrides for now."""

    TARGET_WIDTH = 1920
    TARGET_HEIGHT = 1080

    def detect_target(self) -> RuntimeTarget | None:
        width = int(os.getenv("PROXDECK_TARGET_WIDTH", str(self.TARGET_WIDTH)))
        height = int(os.getenv("PROXDECK_TARGET_HEIGHT", str(self.TARGET_HEIGHT)))
        detected = os.getenv("PROXDECK_DETECTED_MONITOR")
        if not detected:
            return None

        return RuntimeTarget(
            monitor_name=detected,
            width=width,
            height=height,
            x=int(os.getenv("PROXDECK_TARGET_X", "0")),
            y=int(os.getenv("PROXDECK_TARGET_Y", "0")),
        )
