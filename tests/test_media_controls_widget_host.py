from proxdeck.presentation.widgets.media_controls_widget_host import (
    MediaAction,
    VK_MEDIA_NEXT_TRACK,
    VK_MEDIA_PLAY_PAUSE,
    VK_MEDIA_PREV_TRACK,
    media_actions,
)


def test_media_actions_expose_transport_buttons() -> None:
    assert media_actions() == (
        MediaAction(label="Previous", virtual_key=VK_MEDIA_PREV_TRACK),
        MediaAction(label="Play/Pause", virtual_key=VK_MEDIA_PLAY_PAUSE),
        MediaAction(label="Next", virtual_key=VK_MEDIA_NEXT_TRACK),
    )
