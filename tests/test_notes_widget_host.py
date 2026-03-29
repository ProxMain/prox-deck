def test_notes_widget_host_builds_preview_payload() -> None:
    content = "Remember to tune the stream layout before going live."
    preview = content[:140]

    assert preview == "Remember to tune the stream layout before going live."
