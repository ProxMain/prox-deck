from __future__ import annotations

from urllib.parse import urlparse

from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance

try:
    from PySide6.QtCore import QUrl, Qt
    from PySide6.QtGui import QColor
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QUrl = object
    Qt = object
    QColor = object
    QWebEnginePage = object
    QWebEngineProfile = object
    QWebEngineSettings = object
    QWebEngineView = object
    QFrame = object
    QLabel = object
    QVBoxLayout = object
    QWidget = object


MOBILE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
    "Mobile/15E148 Safari/604.1"
)


def normalize_web_widget_url(raw_url: object) -> str:
    candidate = str(raw_url or "").strip()
    if not candidate:
        return "https://example.com"

    parsed = urlparse(candidate)
    if parsed.scheme:
        return candidate
    return f"https://{candidate}"


def build_web_widget_user_agent(force_mobile: bool) -> str | None:
    if force_mobile:
        return MOBILE_USER_AGENT
    return None


def build_web_widget_host(
    widget_instance: WidgetInstance,
    widget_definition: WidgetDefinition | None,
    footer: str,
) -> QWidget:
    if QWebEngineView is object or Qt is object:
        return _build_browser_unavailable_card(widget_instance, footer)

    url = normalize_web_widget_url(widget_instance.settings.get("url"))
    mobile = bool(widget_instance.settings.get("force_mobile", False))

    container = QFrame()
    container.setStyleSheet(
        "QFrame {"
        "background: #05080C;"
        "border: none;"
        "border-radius: 0px;"
        "}"
    )

    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    browser_view = QWebEngineView(container)
    browser_view.setPage(_build_browser_page(container, mobile))
    browser_view.page().setBackgroundColor(QColor("#0F1722"))
    browser_view.setUrl(QUrl(url))
    layout.addWidget(browser_view, 1)
    return container


def _build_browser_page(parent: QWidget, force_mobile: bool) -> QWebEnginePage:
    profile = QWebEngineProfile(parent)
    user_agent = build_web_widget_user_agent(force_mobile)
    if user_agent is not None:
        profile.setHttpUserAgent(user_agent)

    settings = profile.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
    return QWebEnginePage(profile, parent)


def _build_browser_unavailable_card(
    widget_instance: WidgetInstance,
    footer: str,
) -> QWidget:
    url = normalize_web_widget_url(widget_instance.settings.get("url"))
    mobile = bool(widget_instance.settings.get("force_mobile", False))
    card = QFrame()
    card.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
    card.setStyleSheet(
        "QFrame {"
        "background: #101822;"
        "border: none;"
        "border-radius: 14px;"
        "padding: 12px;"
        "}"
        "QLabel { color: #E7EEF7; }"
    )
    layout = QVBoxLayout(card)
    layout.setSpacing(8)
    detail_label = QLabel(
        "Embedded browser support is unavailable in this environment.\n"
        f"Target URL: {url}"
    )
    detail_label.setWordWrap(True)
    detail_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    layout.addWidget(detail_label)
    layout.addStretch(1)
    return card
