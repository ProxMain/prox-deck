from datetime import datetime

from proxdeck.presentation.widgets.clock_widget_host import (
    build_clock_display_state,
    format_clock_timestamp,
)


def test_format_clock_timestamp_returns_time_and_date_lines() -> None:
    time_text, date_text = format_clock_timestamp(datetime(2026, 3, 29, 14, 5))

    assert time_text == "14:05"
    assert date_text == "Zondag, 29 Maart 2026"


def test_build_clock_display_state_returns_dutch_hud_fields() -> None:
    state = build_clock_display_state(datetime(2026, 3, 29, 14, 5, 7))

    assert state.time_text == "14:05"
    assert state.day_name == "Zondag"
    assert state.date_text == "29 Maart 2026"
    assert (state.hour, state.minute, state.second) == (14, 5, 7)
