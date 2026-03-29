from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from proxdeck.bootstrap.app_factory import AppFactory

try:
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError as error:  # pragma: no cover - startup guard
    raise SystemExit(
        "PySide6 is not installed. Install project dependencies before running the app."
    ) from error


def main() -> int:
    app = QApplication(sys.argv)
    proxdeck = AppFactory(project_root=PROJECT_ROOT).create()
    proxdeck.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
