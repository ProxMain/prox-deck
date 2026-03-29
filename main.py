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


def main() -> int:
    project_root = Path(__file__).resolve().parent
    app = QApplication(sys.argv)
    proxdeck = AppFactory(project_root=project_root).create()
    window = proxdeck.build_window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
