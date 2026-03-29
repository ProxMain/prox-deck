from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from proxdeck.domain.value_objects.app_version import AppVersion


APP_VERSION = AppVersion.parse("0.1.0")


@dataclass(frozen=True)
class AppPaths:
    project_root: Path
    storage_root: Path
    screen_state_path: Path
    builtin_widgets_root: Path
    installable_widgets_root: Path


def build_app_paths(project_root: Path) -> AppPaths:
    storage_root = project_root / ".proxdeck"
    return AppPaths(
        project_root=project_root,
        storage_root=storage_root,
        screen_state_path=storage_root / "screens.json",
        builtin_widgets_root=project_root / "widgets",
        installable_widgets_root=project_root / "installable_widgets",
    )
