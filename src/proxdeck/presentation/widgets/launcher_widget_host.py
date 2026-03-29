from __future__ import annotations

from dataclasses import dataclass

from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance

try:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QUrl = object
    QDesktopServices = object
    QFrame = object
    QGridLayout = object
    QLabel = object
    QPushButton = object
    QVBoxLayout = object
    QWidget = object


@dataclass(frozen=True)
class LauncherItem:
    label: str
    target: str


def extract_launcher_items(settings: dict[str, object]) -> tuple[LauncherItem, ...]:
    raw_items = settings.get("items")
    if not isinstance(raw_items, list):
        return _default_launcher_items()

    items: list[LauncherItem] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).strip()
        target = str(item.get("target", "")).strip()
        if not label or not target:
            continue
        items.append(LauncherItem(label=label, target=target))

    return tuple(items) or _default_launcher_items()


def build_launcher_widget_host(
    widget_instance: WidgetInstance,
    widget_definition: WidgetDefinition | None,
    footer: str,
) -> QWidget:
    card = QFrame()
    card.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
    card.setStyleSheet(
        "QFrame {"
        "background: #0F1B13;"
        "border: none;"
        "border-radius: 0px;"
        "padding: 12px;"
        "}"
        "QLabel { color: #EAFBF0; }"
        "QPushButton {"
        "background: #1E3526;"
        "color: #EAFBF0;"
        "border: 1px solid #4E8E63;"
        "border-radius: 12px;"
        "padding: 12px;"
        "font-size: 14px;"
        "font-weight: 700;"
        "}"
        "QPushButton:hover { background: #274530; }"
    )
    layout = QVBoxLayout(card)
    layout.setSpacing(8)

    status_label = QLabel("Quick actions ready.")
    status_label.setWordWrap(True)
    status_label.setStyleSheet("font-size: 12px; color: #B8D8C3;")
    layout.addWidget(status_label)

    grid = QGridLayout()
    grid.setSpacing(8)
    for index, item in enumerate(extract_launcher_items(widget_instance.settings)):
        button = QPushButton(item.label)
        button.clicked.connect(
            lambda _checked=False, target=item.target: _launch_target(target, status_label)
        )
        grid.addWidget(button, index // 2, index % 2)
    layout.addLayout(grid)

    layout.addStretch(1)
    return card


def _launch_target(target: str, status_label: QLabel) -> None:
    if QDesktopServices is object or QUrl is object:
        status_label.setText(f"Cannot launch {target} in this environment.")
        return

    success = QDesktopServices.openUrl(QUrl(target))
    if success:
        status_label.setText(f"Launched {target}")
    else:
        status_label.setText(f"Failed to launch {target}")


def _default_launcher_items() -> tuple[LauncherItem, ...]:
    return (
        LauncherItem(label="GitHub", target="https://github.com"),
        LauncherItem(label="OpenAI", target="https://openai.com"),
        LauncherItem(label="YouTube", target="https://youtube.com"),
        LauncherItem(label="Settings", target="ms-settings:"),
    )
