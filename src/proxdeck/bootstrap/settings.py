from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    project_root: Path
    storage_root: Path
    screen_state_path: Path


def build_app_paths(project_root: Path) -> AppPaths:
    storage_root = project_root / ".proxdeck"
    return AppPaths(
        project_root=project_root,
        storage_root=storage_root,
        screen_state_path=storage_root / "screens.json",
    )
