from proxdeck.presentation.widgets.web_widget_host import (
    MOBILE_USER_AGENT,
    build_web_widget_user_agent,
    normalize_web_widget_url,
)


def test_normalize_web_widget_url_adds_https_scheme() -> None:
    assert normalize_web_widget_url("example.com") == "https://example.com"


def test_normalize_web_widget_url_keeps_existing_scheme() -> None:
    assert normalize_web_widget_url("https://openai.com") == "https://openai.com"


def test_normalize_web_widget_url_uses_default_for_empty_value() -> None:
    assert normalize_web_widget_url("") == "https://example.com"


def test_build_web_widget_user_agent_returns_mobile_profile() -> None:
    assert build_web_widget_user_agent(True) == MOBILE_USER_AGENT


def test_build_web_widget_user_agent_returns_none_for_desktop_mode() -> None:
    assert build_web_widget_user_agent(False) is None
