from proxdeck.application.services.stream_deck_action_executor import (
    StreamDeckActionExecutor,
    StreamDeckActionResult,
)
from proxdeck.application.services.stream_deck_configuration import (
    build_default_stream_deck_settings,
    parse_stream_deck_settings,
    visible_stream_deck_button_count,
)
from proxdeck.domain.models.stream_deck import StreamDeckButtonDefinition


class StubLaunchTargetExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    def launch(self, target: str, arguments: list[str]) -> StreamDeckActionResult:
        self.calls.append((target, arguments))
        return StreamDeckActionResult(success=True, message=f"Launched {target}")


def test_parse_stream_deck_settings_uses_defaults() -> None:
    settings = parse_stream_deck_settings({})

    assert settings.size_variant == "1/6"
    assert settings.buttons[0].label == "Browser"
    assert settings.buttons[0].icon == "asset:stream_deck_browser.svg"
    assert settings.buttons[0].action_type == "launch"


def test_build_default_stream_deck_settings_uses_requested_variant() -> None:
    settings = build_default_stream_deck_settings("2/6-tall")

    assert settings["size_variant"] == "2/6-tall"
    assert settings["buttons"][2]["action_type"] == "group"
    assert settings["buttons"][2]["action_config"]["children"][0]["label"] == "Chat"


def test_stream_deck_action_executor_launches_valid_button() -> None:
    launcher = StubLaunchTargetExecutor()
    executor = StreamDeckActionExecutor(launcher)

    result = executor.execute(
        StreamDeckButtonDefinition(
            button_id="discord",
            label="Discord",
            icon="DSC",
            action_type="launch",
            action_config={"target": "discord.exe", "arguments": ["--start-minimized"]},
        )
    )

    assert result.success is True
    assert launcher.calls == [("discord.exe", ["--start-minimized"])]


def test_stream_deck_action_executor_rejects_missing_target() -> None:
    launcher = StubLaunchTargetExecutor()
    executor = StreamDeckActionExecutor(launcher)

    result = executor.execute(
        StreamDeckButtonDefinition(
            button_id="empty",
            label="Empty",
            icon=None,
            action_type="launch",
            action_config={},
        )
    )

    assert result.success is False
    assert "missing a launch target" in result.message
    assert launcher.calls == []


def test_parse_stream_deck_settings_maps_legacy_icon_codes_to_assets() -> None:
    settings = parse_stream_deck_settings(
        {
            "buttons": [
                {
                    "id": "browser",
                    "label": "Browser",
                    "icon": "WWW",
                    "action_type": "launch",
                    "action_config": {"target": "https://example.com"},
                },
                {
                    "id": "folder",
                    "label": "Folder",
                    "icon": "DIR",
                    "action_type": "group",
                    "action_config": {"children": []},
                },
            ]
        }
    )

    assert settings.buttons[0].icon == "asset:stream_deck_browser.svg"
    assert settings.buttons[1].icon == "asset:stream_deck_folder.svg"


def test_visible_stream_deck_button_count_matches_dense_runtime_layout() -> None:
    assert visible_stream_deck_button_count("1/6") == 16
    assert visible_stream_deck_button_count("2/6-tall") == 32
