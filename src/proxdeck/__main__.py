from __future__ import annotations

import sys
from pathlib import Path

from proxdeck.bootstrap.app_factory import AppFactory

try:
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError as error:  # pragma: no cover - startup guard
    raise SystemExit(
        "PySide6 is not installed. Install project dependencies before running the app."
    ) from error


def resolve_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    app = QApplication(sys.argv)
    proxdeck = AppFactory(project_root=resolve_project_root()).create()
    proxdeck.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
