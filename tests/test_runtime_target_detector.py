import os

from proxdeck.infrastructure.system.qt_screen_runtime_target_detector import (
    QtScreenRuntimeTargetDetector,
)
from proxdeck.infrastructure.system.screen_snapshot import ScreenSnapshot


def test_runtime_target_detector_matches_screen_by_resolution() -> None:
    detector = QtScreenRuntimeTargetDetector(
        screen_provider=lambda: [
            ScreenSnapshot(name="Primary", width=2560, height=1440, x=0, y=0),
            ScreenSnapshot(name="Xeneon Edge", width=1920, height=1080, x=2560, y=0),
        ]
    )

    target = detector.detect_target()

    assert target is not None
    assert target.monitor_name == "Xeneon Edge"
    assert target.width == 1920
    assert target.height == 1080
    assert target.x == 2560


def test_runtime_target_detector_returns_none_when_no_matching_screen() -> None:
    detector = QtScreenRuntimeTargetDetector(
        screen_provider=lambda: [
            ScreenSnapshot(name="Primary", width=2560, height=1440, x=0, y=0),
        ]
    )

    assert detector.detect_target() is None


def test_runtime_target_detector_prefers_explicit_override() -> None:
    original_env = {
        "PROXDECK_DETECTED_MONITOR": os.getenv("PROXDECK_DETECTED_MONITOR"),
        "PROXDECK_TARGET_WIDTH": os.getenv("PROXDECK_TARGET_WIDTH"),
        "PROXDECK_TARGET_HEIGHT": os.getenv("PROXDECK_TARGET_HEIGHT"),
        "PROXDECK_TARGET_X": os.getenv("PROXDECK_TARGET_X"),
        "PROXDECK_TARGET_Y": os.getenv("PROXDECK_TARGET_Y"),
    }
    os.environ["PROXDECK_DETECTED_MONITOR"] = "Forced Edge"
    os.environ["PROXDECK_TARGET_WIDTH"] = "1600"
    os.environ["PROXDECK_TARGET_HEIGHT"] = "720"
    os.environ["PROXDECK_TARGET_X"] = "100"
    os.environ["PROXDECK_TARGET_Y"] = "200"

    try:
        detector = QtScreenRuntimeTargetDetector(screen_provider=lambda: [])
        target = detector.detect_target()
    finally:
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    assert target is not None
    assert target.monitor_name == "Forced Edge"
    assert target.width == 1600
    assert target.height == 720
    assert target.x == 100
    assert target.y == 200
