from __future__ import annotations

import ctypes
from dataclasses import dataclass

from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance

try:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QTimer = object
    QFrame = object
    QLabel = object
    QVBoxLayout = object
    QWidget = object


@dataclass(frozen=True)
class SystemStatsSnapshot:
    cpu_percent: float | None
    memory_percent: float | None


class WindowsSystemStatsProvider:
    def __init__(self) -> None:
        self._previous_cpu_times: tuple[int, int, int] | None = None

    def read_snapshot(self) -> SystemStatsSnapshot:
        return SystemStatsSnapshot(
            cpu_percent=self._read_cpu_percent(),
            memory_percent=self._read_memory_percent(),
        )

    def _read_cpu_percent(self) -> float | None:
        file_time = _get_filetime_structure_type()
        idle_time = file_time()
        kernel_time = file_time()
        user_time = file_time()

        if not ctypes.windll.kernel32.GetSystemTimes(
            ctypes.byref(idle_time),
            ctypes.byref(kernel_time),
            ctypes.byref(user_time),
        ):
            return None

        current_times = (
            _filetime_to_int(idle_time),
            _filetime_to_int(kernel_time),
            _filetime_to_int(user_time),
        )
        previous_times = self._previous_cpu_times
        self._previous_cpu_times = current_times
        if previous_times is None:
            return None

        idle_delta = current_times[0] - previous_times[0]
        total_delta = (
            (current_times[1] - previous_times[1]) + (current_times[2] - previous_times[2])
        )
        if total_delta <= 0:
            return None

        busy_ratio = max(0.0, min(1.0, 1.0 - (idle_delta / total_delta)))
        return round(busy_ratio * 100, 1)

    def _read_memory_percent(self) -> float | None:
        status = _get_memory_status_ex_structure_type()()
        status.dwLength = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return None
        return round(float(status.dwMemoryLoad), 1)


def format_system_stats_snapshot(snapshot: SystemStatsSnapshot) -> tuple[str, str]:
    cpu_line = _format_metric("CPU", snapshot.cpu_percent)
    memory_line = _format_metric("Memory", snapshot.memory_percent)
    return cpu_line, memory_line


def build_system_stats_widget_host(
    widget_instance: WidgetInstance,
    widget_definition: WidgetDefinition | None,
    footer: str,
    provider: WindowsSystemStatsProvider | None = None,
) -> QWidget:
    provider = provider or WindowsSystemStatsProvider()
    card = QFrame()
    card.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
    card.setStyleSheet(
        "QFrame {"
        "background: #101822;"
        "border: 2px solid #F07A9B;"
        "border-radius: 14px;"
        "padding: 12px;"
        "}"
        "QLabel { color: #E7EEF7; }"
    )
    layout = QVBoxLayout(card)
    layout.setSpacing(8)

    title_label = QLabel("System Stats")
    title_label.setStyleSheet("font-size: 20px; font-weight: 700;")
    layout.addWidget(title_label)

    subtitle_label = QLabel(widget_instance.instance_id)
    subtitle_label.setStyleSheet("font-size: 13px; color: #9DB1C7;")
    layout.addWidget(subtitle_label)

    cpu_label = QLabel()
    cpu_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #F9D2DD;")
    layout.addWidget(cpu_label)

    memory_label = QLabel()
    memory_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #F9D2DD;")
    layout.addWidget(memory_label)

    hint_label = QLabel("Live local machine metrics update automatically.")
    hint_label.setWordWrap(True)
    hint_label.setStyleSheet("font-size: 12px; color: #9DB1C7;")
    layout.addWidget(hint_label)

    footer_label = QLabel(footer)
    footer_label.setWordWrap(True)
    footer_label.setStyleSheet("font-size: 11px; color: #89A0B8;")
    layout.addWidget(footer_label)
    layout.addStretch(1)

    def refresh_labels() -> None:
        cpu_line, memory_line = format_system_stats_snapshot(provider.read_snapshot())
        cpu_label.setText(cpu_line)
        memory_label.setText(memory_line)

    refresh_labels()
    if QTimer is not object:
        timer = QTimer(card)
        timer.setInterval(1500)
        timer.timeout.connect(refresh_labels)
        timer.start()

    return card


def _format_metric(label: str, value: float | None) -> str:
    if value is None:
        return f"{label}: unavailable"
    return f"{label}: {value:.1f}%"


def _get_filetime_structure_type():
    class FileTime(ctypes.Structure):
        _fields_ = [
            ("dwLowDateTime", ctypes.c_ulong),
            ("dwHighDateTime", ctypes.c_ulong),
        ]

    return FileTime


def _get_memory_status_ex_structure_type():
    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    return MemoryStatusEx


def _filetime_to_int(value) -> int:
    return (value.dwHighDateTime << 32) | value.dwLowDateTime
