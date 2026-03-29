from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from proxdeck.domain.value_objects.app_version import AppVersion


APP_VERSION = AppVersion.parse("1.0.0")
APP_RELEASE = "1.0.0-alpha"
PACKAGE_VERSION = "1.0.0a0"


@dataclass(frozen=True)
class AppPaths:
    storage_root: Path
    screen_state_path: Path
    builtin_widgets_root: Path
    bundled_installable_widgets_root: Path
    user_installable_widgets_root: Path


def build_app_paths(project_root: Path) -> AppPaths:
    bundled_root = resolve_bundled_root(project_root)
    storage_root = resolve_storage_root(project_root)
    return AppPaths(
        storage_root=storage_root,
        screen_state_path=storage_root / "screens.json",
        builtin_widgets_root=bundled_root / "widgets",
        bundled_installable_widgets_root=bundled_root / "installable_widgets",
        user_installable_widgets_root=storage_root / "installable_widgets",
    )


def resolve_bundled_root(project_root: Path) -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass is not None:
            return Path(meipass)
    return project_root


def resolve_storage_root(project_root: Path) -> Path:
    if not getattr(sys, "frozen", False):
        return project_root / ".proxdeck"

    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "ProxDeck"

    app_data = os.getenv("APPDATA")
    if app_data:
        return Path(app_data) / "ProxDeck"

    return Path.home() / "AppData" / "Local" / "ProxDeck"
