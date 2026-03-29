from proxdeck.presentation.widgets.system_stats_widget_host import (
    SystemStatsSnapshot,
    format_system_stats_snapshot,
)


def test_format_system_stats_snapshot_formats_available_values() -> None:
    cpu_line, memory_line = format_system_stats_snapshot(
        SystemStatsSnapshot(cpu_percent=18.4, memory_percent=61.0)
    )

    assert cpu_line == "CPU: 18.4%"
    assert memory_line == "Memory: 61.0%"


def test_format_system_stats_snapshot_handles_unavailable_values() -> None:
    cpu_line, memory_line = format_system_stats_snapshot(
        SystemStatsSnapshot(cpu_percent=None, memory_percent=None)
    )

    assert cpu_line == "CPU: unavailable"
    assert memory_line == "Memory: unavailable"
