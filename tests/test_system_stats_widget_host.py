from datetime import datetime

from proxdeck.domain.value_objects.widget_placement import WidgetPlacement
from proxdeck.domain.value_objects.widget_size import WidgetSize, normalize_size_preset
from proxdeck.presentation.widgets.system_stats_widget_host import (
    SystemStatsSnapshot,
    build_system_stats_display_state,
    format_system_stats_snapshot,
    select_system_stats_layout_variant,
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


def test_select_system_stats_layout_variant_uses_compact_for_one_cell() -> None:
    assert select_system_stats_layout_variant(WidgetPlacement(column=0, row=0, width=1, height=1)) == "compact"


def test_select_system_stats_layout_variant_uses_circular_for_multi_cell_widget() -> None:
    assert select_system_stats_layout_variant(WidgetPlacement(column=0, row=0, width=1, height=2)) == "circular"


def test_widget_size_supports_vertical_and_horizontal_alias_presets() -> None:
    _, width, height = WidgetSize.from_preset("2/6-vertical")
    assert (width, height) == (1, 2)

    _, width, height = WidgetSize.from_preset("2/6-horizontal")
    assert (width, height) == (2, 1)


def test_normalize_size_preset_maps_builder_aliases() -> None:
    assert normalize_size_preset("2T") == "2/6-tall"
    assert normalize_size_preset("2W") == "2/6-wide"
    assert normalize_size_preset("6") == "6/6"


def test_build_display_state_for_compact_variant_keeps_small_core_metrics() -> None:
    state = build_system_stats_display_state(
        snapshot=SystemStatsSnapshot(
            cpu_percent=21.0,
            memory_percent=63.0,
            gpu_percent=14.0,
            cpu_temp_c=52.0,
            case_temp_c=None,
            gpu_temp_c=57.0,
        ),
        placement=WidgetPlacement(column=0, row=0, width=1, height=1),
        moment=datetime(2026, 3, 29, 14, 5),
    )

    assert state.layout_variant == "compact"
    assert state.primary_metric.label == "CPU"
    assert state.primary_metric.value_text == "21%"
    assert state.secondary_metric.label == "GPU"
    assert state.secondary_metric.value_text == "14%"
    assert [metric.label for metric in state.gauge_metrics] == ["CPU", "GPU", "CPU TEMP", "GPU TEMP"]
    assert [metric.label for metric in state.temperature_nodes] == ["CPU TEMP", "CASE TEMP", "GPU TEMP"]
    assert state.temperature_nodes[1].value_text == "--"


def test_build_display_state_for_circular_variant_exposes_primary_secondary_and_temperature_nodes() -> None:
    state = build_system_stats_display_state(
        snapshot=SystemStatsSnapshot(
            cpu_percent=42.0,
            memory_percent=66.0,
            gpu_percent=57.0,
            cpu_temp_c=68.0,
            case_temp_c=43.0,
            gpu_temp_c=None,
            cpu_clock_ghz=None,
            memory_used_gb=10.4,
            memory_total_gb=31.8,
        ),
        placement=WidgetPlacement(column=0, row=0, width=1, height=2),
        moment=datetime(2026, 3, 29, 14, 5),
    )

    assert state.layout_variant == "circular"
    assert state.primary_metric.label == "CPU"
    assert state.primary_metric.value_text == "42%"
    assert state.secondary_metric.label == "GPU"
    assert state.secondary_metric.value_text == "57%"
    assert [metric.label for metric in state.gauge_metrics] == ["CPU", "GPU", "CPU TEMP", "GPU TEMP"]
    assert state.gauge_metrics[3].detail_text == "CASE 43C"
    assert [metric.label for metric in state.temperature_nodes] == ["CPU TEMP", "CASE TEMP", "GPU TEMP"]
    assert state.temperature_nodes[1].value_text == "43C"
