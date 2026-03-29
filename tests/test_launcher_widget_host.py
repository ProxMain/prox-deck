from proxdeck.presentation.widgets.launcher_widget_host import (
    LauncherItem,
    extract_launcher_items,
)


def test_extract_launcher_items_uses_valid_custom_items() -> None:
    items = extract_launcher_items(
        {
            "items": [
                {"label": "Docs", "target": "https://example.com/docs"},
                {"label": "Settings", "target": "ms-settings:"},
            ]
        }
    )

    assert items == (
        LauncherItem(label="Docs", target="https://example.com/docs"),
        LauncherItem(label="Settings", target="ms-settings:"),
    )


def test_extract_launcher_items_falls_back_to_defaults() -> None:
    items = extract_launcher_items({})

    assert items[0] == LauncherItem(label="GitHub", target="https://github.com")
    assert items[3] == LauncherItem(label="Settings", target="ms-settings:")
