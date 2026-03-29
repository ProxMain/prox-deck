from datetime import datetime

from proxdeck.presentation.widgets.clock_widget_host import format_clock_timestamp


def test_format_clock_timestamp_returns_time_and_date_lines() -> None:
    time_text, date_text = format_clock_timestamp(datetime(2026, 3, 29, 14, 5))

    assert time_text == "14:05"
    assert date_text == "Sunday, 29 March"
