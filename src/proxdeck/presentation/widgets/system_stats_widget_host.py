from __future__ import annotations

import ctypes
import json
import math
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime

from proxdeck.domain.models.widget_definition import WidgetDefinition
from proxdeck.domain.models.widget_instance import WidgetInstance
from proxdeck.domain.value_objects.widget_placement import WidgetPlacement
from proxdeck.infrastructure.system.hwinfo_bridge import HWiNFOBridge

try:
    from PySide6.QtCore import QPointF, QRectF, QSize, QTimer, Qt
    from PySide6.QtGui import QColor, QConicalGradient, QFont, QLinearGradient, QPainter, QPen, QRadialGradient
    from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget
except ModuleNotFoundError:  # pragma: no cover - optional during headless tests
    QPointF = object
    QRectF = object
    QSize = object
    QTimer = object
    Qt = object
    QColor = object
    QConicalGradient = object
    QFont = object
    QLinearGradient = object
    QPainter = object
    QPen = object
    QRadialGradient = object
    QFrame = object
    QVBoxLayout = object
    QWidget = object


@dataclass(frozen=True)
class SystemStatsSnapshot:
    cpu_percent: float | None
    memory_percent: float | None
    gpu_percent: float | None = None
    cpu_temp_c: float | None = None
    case_temp_c: float | None = None
    gpu_temp_c: float | None = None
    cpu_clock_ghz: float | None = None
    memory_used_gb: float | None = None
    memory_total_gb: float | None = None


@dataclass(frozen=True)
class DialMetricDisplay:
    label: str
    value: float | None
    value_text: str
    detail_text: str
    accent: str

    @property
    def normalized_value(self) -> float:
        if self.value is None:
            return 0.0
        return max(0.0, min(100.0, self.value))


@dataclass(frozen=True)
class TemperatureNodeDisplay:
    label: str
    value_text: str
    detail_text: str
    accent: str


@dataclass(frozen=True)
class SystemStatsDisplayState:
    layout_variant: str
    overline_text: str
    primary_metric: DialMetricDisplay
    secondary_metric: DialMetricDisplay
    gauge_metrics: tuple[DialMetricDisplay, ...]
    temperature_nodes: tuple[TemperatureNodeDisplay, ...]


class WindowsSystemStatsProvider:
    def __init__(self, start_background_polling: bool = True) -> None:
        self._previous_cpu_times: tuple[int, int, int] | None = None
        self._gpu_counter_query: ctypes.c_void_p | None = None
        self._gpu_counter_handles: list[ctypes.c_void_p] = []
        self._gpu_counter_ready = False
        self._gpu_fallback_last_sample_at = 0.0
        self._gpu_fallback_cached_value: float | None = None
        self._lhm_last_sample_at = 0.0
        self._lhm_cached_metrics: dict[str, float | None] = {}
        self._hwinfo_bridge = HWiNFOBridge()
        self._last_hwinfo_complete_at = 0.0
        self._cached_snapshot = SystemStatsSnapshot(
            cpu_percent=None,
            memory_percent=None,
            gpu_percent=None,
            cpu_temp_c=None,
            case_temp_c=None,
            gpu_temp_c=None,
            cpu_clock_ghz=None,
            memory_used_gb=None,
            memory_total_gb=None,
        )
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._poll_thread: threading.Thread | None = None
        if start_background_polling:
            self._cached_snapshot = self._poll_once()
            self._poll_thread = threading.Thread(target=self._poll_loop, name="system-stats-provider", daemon=True)
            self._poll_thread.start()

    def read_snapshot(self) -> SystemStatsSnapshot:
        if self._poll_thread is None:
            return self._poll_once()
        with self._lock:
            return self._cached_snapshot

    def close(self) -> None:
        self._stop_event.set()
        if self._poll_thread is not None:
            self._poll_thread.join(timeout=0.2)

    def _poll_loop(self) -> None:
        while not self._stop_event.wait(1.5):
            snapshot = self._poll_once()
            with self._lock:
                self._cached_snapshot = snapshot

    def _poll_once(self) -> SystemStatsSnapshot:
        memory_metrics = self._read_memory_metrics()
        hwinfo_metrics = self._hwinfo_bridge.read_metrics()
        if self._has_complete_hwinfo_metrics(hwinfo_metrics):
            self._last_hwinfo_complete_at = time.monotonic()
            lhm_metrics = {}
        else:
            lhm_metrics = self._read_lhm_metrics()
        return SystemStatsSnapshot(
            cpu_percent=self._read_cpu_percent(),
            memory_percent=memory_metrics[0],
            gpu_percent=hwinfo_metrics.gpu_percent if hwinfo_metrics.gpu_percent is not None else self._read_gpu_percent(),
            cpu_temp_c=hwinfo_metrics.cpu_temp_c or lhm_metrics.get("cpu_temp_c"),
            case_temp_c=hwinfo_metrics.case_temp_c or lhm_metrics.get("case_temp_c"),
            gpu_temp_c=hwinfo_metrics.gpu_temp_c or lhm_metrics.get("gpu_temp_c"),
            cpu_clock_ghz=None,
            memory_used_gb=memory_metrics[1],
            memory_total_gb=memory_metrics[2],
        )

    def _read_cpu_percent(self) -> float | None:
        if not hasattr(ctypes, "windll"):
            return None

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
        total_delta = (current_times[1] - previous_times[1]) + (current_times[2] - previous_times[2])
        if total_delta <= 0:
            return None

        busy_ratio = max(0.0, min(1.0, 1.0 - (idle_delta / total_delta)))
        return round(busy_ratio * 100, 1)

    def _read_memory_metrics(self) -> tuple[float | None, float | None, float | None]:
        if not hasattr(ctypes, "windll"):
            return None, None, None

        status = _get_memory_status_ex_structure_type()()
        status.dwLength = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return None, None, None

        total_gb = round(status.ullTotalPhys / (1024**3), 1)
        available_gb = round(status.ullAvailPhys / (1024**3), 1)
        used_gb = round(total_gb - available_gb, 1)
        return round(float(status.dwMemoryLoad), 1), used_gb, total_gb

    def _read_gpu_percent(self) -> float | None:
        if time.monotonic() - self._last_hwinfo_complete_at < 30.0:
            return self._gpu_fallback_cached_value
        if not hasattr(ctypes, "windll"):
            return self._read_gpu_percent_from_powershell()

        if self._gpu_counter_query is None and not self._initialize_gpu_counters():
            return self._read_gpu_percent_from_powershell()
        if self._gpu_counter_query is None:
            return self._read_gpu_percent_from_powershell()

        pdh = ctypes.windll.pdh
        if pdh.PdhCollectQueryData(self._gpu_counter_query) != 0:
            return self._read_gpu_percent_from_powershell()

        if not self._gpu_counter_ready:
            self._gpu_counter_ready = True
            return self._read_gpu_percent_from_powershell()

        total_percent = 0.0
        for counter_handle in self._gpu_counter_handles:
            value = _get_pdh_fmt_countervalue_double_type()()
            counter_type = ctypes.c_ulong()
            status = pdh.PdhGetFormattedCounterValue(
                counter_handle,
                _PDH_FMT_DOUBLE,
                ctypes.byref(counter_type),
                ctypes.byref(value),
            )
            if status != 0:
                continue
            total_percent += max(0.0, value.doubleValue)

        if total_percent <= 0:
            fallback_value = self._read_gpu_percent_from_powershell()
            if fallback_value is not None:
                return fallback_value
            return 0.0
        return round(min(100.0, total_percent), 1)

    def _initialize_gpu_counters(self) -> bool:
        pdh = ctypes.windll.pdh
        query_handle = ctypes.c_void_p()
        status = pdh.PdhOpenQueryW(None, 0, ctypes.byref(query_handle))
        if status != 0:
            return False

        paths = self._expand_gpu_counter_paths()
        if not paths:
            pdh.PdhCloseQuery(query_handle)
            return False

        counter_handles: list[ctypes.c_void_p] = []
        add_counter = getattr(pdh, "PdhAddEnglishCounterW", None)
        if add_counter is None:
            add_counter = pdh.PdhAddCounterW

        for path in paths:
            counter_handle = ctypes.c_void_p()
            status = add_counter(query_handle, path, 0, ctypes.byref(counter_handle))
            if status == 0:
                counter_handles.append(counter_handle)

        if not counter_handles:
            pdh.PdhCloseQuery(query_handle)
            return False

        self._gpu_counter_query = query_handle
        self._gpu_counter_handles = counter_handles
        pdh.PdhCollectQueryData(self._gpu_counter_query)
        self._gpu_counter_ready = True
        return True

    def _expand_gpu_counter_paths(self) -> list[str]:
        pdh = ctypes.windll.pdh
        wildcard_path = "\\GPU Engine(*)\\Utilization Percentage"
        required_length = ctypes.c_ulong(0)
        status = pdh.PdhExpandWildCardPathW(
            None,
            wildcard_path,
            None,
            ctypes.byref(required_length),
            0,
        )
        if status not in {_PDH_MORE_DATA, 0} or required_length.value <= 0:
            return []

        buffer = ctypes.create_unicode_buffer(required_length.value)
        status = pdh.PdhExpandWildCardPathW(
            None,
            wildcard_path,
            buffer,
            ctypes.byref(required_length),
            0,
        )
        if status != 0:
            return []

        raw_paths = buffer[: required_length.value]
        return [
            path
            for path in raw_paths.split("\x00")
            if path and _is_relevant_gpu_counter_path(path)
        ]

    def __del__(self) -> None:
        if self._gpu_counter_query is None or not hasattr(ctypes, "windll"):
            return
        try:
            ctypes.windll.pdh.PdhCloseQuery(self._gpu_counter_query)
        except Exception:
            pass

    def _read_gpu_percent_from_powershell(self) -> float | None:
        now = time.monotonic()
        if now - self._gpu_fallback_last_sample_at < 3.0:
            return self._gpu_fallback_cached_value

        self._gpu_fallback_last_sample_at = now
        command = (
            "$sum = (Get-Counter '\\GPU Engine(*)\\Utilization Percentage' | "
            "Select-Object -ExpandProperty CounterSamples | "
            "Where-Object { $_.Path -match 'engtype_(3D|Compute|Cuda|Copy|VideoDecode|VideoEncode)' } | "
            "Measure-Object -Property CookedValue -Sum).Sum; "
            "if ($null -eq $sum) { '' } "
            "else { [string]::Format([System.Globalization.CultureInfo]::InvariantCulture, '{0:0.0}', [double]$sum) }"
        )
        try:
            completed = subprocess.run(
                [
                    "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    command,
                ],
                capture_output=True,
                text=True,
                timeout=4.0,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return self._gpu_fallback_cached_value

        if completed.returncode != 0:
            return self._gpu_fallback_cached_value

        stdout = completed.stdout.strip()
        if not stdout:
            self._gpu_fallback_cached_value = 0.0
            return self._gpu_fallback_cached_value

        try:
            sampled_value = float(stdout.replace(",", "."))
        except ValueError:
            return self._gpu_fallback_cached_value

        self._gpu_fallback_cached_value = round(min(100.0, max(0.0, sampled_value)), 1)
        return self._gpu_fallback_cached_value

    def _read_lhm_metrics(self) -> dict[str, float | None]:
        now = time.monotonic()
        if now - self._lhm_last_sample_at < 15.0:
            return self._lhm_cached_metrics

        self._lhm_last_sample_at = now
        dll_path = (
            "C:\\Program Files (x86)\\RivaTuner Statistics Server\\Plugins\\Client\\LHMDataProvider\\LibreHardwareMonitorLib.dll"
        )
        command = (
            f"$asm = [Reflection.Assembly]::LoadFrom('{dll_path}'); "
            "$computer = New-Object LibreHardwareMonitor.Hardware.Computer; "
            "$computer.IsCpuEnabled = $true; "
            "$computer.IsGpuEnabled = $true; "
            "$computer.IsMotherboardEnabled = $true; "
            "$computer.IsControllerEnabled = $true; "
            "$computer.Open(); "
            "foreach ($hardware in $computer.Hardware) { $hardware.Update(); foreach ($sub in $hardware.SubHardware) { $sub.Update() } }; "
            "$rows = foreach ($hardware in $computer.Hardware) { "
            "foreach ($sensor in $hardware.Sensors) { [PSCustomObject]@{ Hardware=$hardware.Name; HardwareType=$hardware.HardwareType.ToString(); Sensor=$sensor.Name; SensorType=$sensor.SensorType.ToString(); Value=$sensor.Value } } "
            "foreach ($sub in $hardware.SubHardware) { foreach ($sensor in $sub.Sensors) { [PSCustomObject]@{ Hardware=$sub.Name; HardwareType=$sub.HardwareType.ToString(); Sensor=$sensor.Name; SensorType=$sensor.SensorType.ToString(); Value=$sensor.Value } } } "
            "}; "
            "$cpu = $rows | Where-Object { $_.HardwareType -eq 'Cpu' -and $_.SensorType -eq 'Temperature' -and $_.Sensor -match 'Tctl|Tdie|Package|Core' } | Select-Object -First 1; "
            "$gpu = $rows | Where-Object { $_.HardwareType -eq 'GpuNvidia' -and $_.SensorType -eq 'Temperature' -and $_.Sensor -eq 'GPU Core' } | Select-Object -First 1; "
            "$case = $rows | Where-Object { $_.HardwareType -match 'Mainboard|SuperIO|Controller' -and $_.SensorType -eq 'Temperature' } | Select-Object -First 1; "
            "[PSCustomObject]@{ cpu_temp_c = if ($cpu -and [double]$cpu.Value -gt 0) { [double]$cpu.Value } else { $null }; "
            "gpu_temp_c = if ($gpu -and [double]$gpu.Value -gt 0) { [double]$gpu.Value } else { $null }; "
            "case_temp_c = if ($case -and [double]$case.Value -gt 0) { [double]$case.Value } else { $null } } | ConvertTo-Json -Compress"
        )
        try:
            completed = subprocess.run(
                [
                    "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    command,
                ],
                capture_output=True,
                text=True,
                timeout=4.0,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return self._lhm_cached_metrics

        if completed.returncode != 0:
            return self._lhm_cached_metrics

        stdout = completed.stdout.strip()
        if not stdout:
            return self._lhm_cached_metrics

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            return self._lhm_cached_metrics

        self._lhm_cached_metrics = {
            "cpu_temp_c": _coerce_optional_float(payload.get("cpu_temp_c")),
            "gpu_temp_c": _coerce_optional_float(payload.get("gpu_temp_c")),
            "case_temp_c": _coerce_optional_float(payload.get("case_temp_c")),
        }
        return self._lhm_cached_metrics

    def _has_complete_hwinfo_metrics(self, metrics) -> bool:
        return (
            metrics.gpu_percent is not None
            and metrics.cpu_temp_c is not None
            and metrics.case_temp_c is not None
            and metrics.gpu_temp_c is not None
        )


def select_system_stats_layout_variant(placement: WidgetPlacement) -> str:
    if placement.width == 1 and placement.height == 1:
        return "compact"
    return "circular"


def build_system_stats_display_state(
    snapshot: SystemStatsSnapshot,
    placement: WidgetPlacement,
    moment: datetime,
) -> SystemStatsDisplayState:
    variant = select_system_stats_layout_variant(placement)
    return SystemStatsDisplayState(
        layout_variant=variant,
        overline_text="",
        primary_metric=_build_dial_metric(
            label="CPU",
            value=snapshot.cpu_percent,
            detail=_percent_status(snapshot.cpu_percent),
            accent="#88F5FF",
        ),
        secondary_metric=_build_dial_metric(
            label="GPU",
            value=snapshot.gpu_percent,
            detail=_status_detail(snapshot.gpu_percent),
            accent="#58D9FF",
        ),
        gauge_metrics=(
            _build_dial_metric("CPU", snapshot.cpu_percent, _percent_status(snapshot.cpu_percent), "#88F5FF"),
            _build_dial_metric("GPU", snapshot.gpu_percent, _status_detail(snapshot.gpu_percent), "#58D9FF"),
            _build_dial_metric("CPU TEMP", snapshot.cpu_temp_c, _temperature_detail(snapshot.cpu_temp_c), "#9EEBFF"),
            _build_dial_metric("GPU TEMP", snapshot.gpu_temp_c, _case_temperature_detail(snapshot.case_temp_c), "#F7D36D"),
        ),
        temperature_nodes=(
            _build_temperature_node("CPU TEMP", snapshot.cpu_temp_c, "#8AF1FF"),
            _build_temperature_node("CASE TEMP", snapshot.case_temp_c, "#F9C95F"),
            _build_temperature_node("GPU TEMP", snapshot.gpu_temp_c, "#6FDBFF"),
        ),
    )


def format_system_stats_snapshot(snapshot: SystemStatsSnapshot) -> tuple[str, str]:
    cpu_line = _format_metric_line("CPU", snapshot.cpu_percent)
    memory_line = _format_metric_line("Memory", snapshot.memory_percent)
    return cpu_line, memory_line


def build_system_stats_widget_host(
    widget_instance: WidgetInstance,
    widget_definition: WidgetDefinition | None,
    footer: str,
    provider: WindowsSystemStatsProvider | None = None,
    live_updates: bool = True,
) -> QWidget:
    owns_provider = provider is None
    provider = provider or WindowsSystemStatsProvider()
    card = QFrame()
    card.setToolTip(footer)
    card.setStyleSheet(
        "QFrame {"
        "background: qradialgradient(cx:0.24, cy:0.18, radius:1.15, fx:0.24, fy:0.18, "
        "stop:0 #10243B, stop:0.34 #091320, stop:0.72 #060C14, stop:1 #04070D);"
        "border: none;"
        "border-radius: 0px;"
        "}"
    )

    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(0)

    dashboard = _build_system_stats_panel(select_system_stats_layout_variant(widget_instance.placement), card)
    layout.addWidget(dashboard)

    def refresh_dashboard() -> None:
        state = build_system_stats_display_state(
            snapshot=provider.read_snapshot(),
            placement=widget_instance.placement,
            moment=datetime.now(),
        )
        dashboard.apply_state(state)

    refresh_dashboard()
    if live_updates and QTimer is not object:
        timer = QTimer(card)
        timer.setInterval(1500)
        timer.timeout.connect(refresh_dashboard)
        timer.start()

    if owns_provider:
        card.destroyed.connect(lambda *_args, tracked_provider=provider: tracked_provider.close())

    return card


class _SystemStatsPanel(QWidget):
    def apply_state(self, state: SystemStatsDisplayState) -> None:  # pragma: no cover - interface
        raise NotImplementedError


def _build_system_stats_panel(layout_variant: str, parent: QWidget | None) -> _SystemStatsPanel:
    if layout_variant == "compact":
        return _CompactCircularTelemetryPanel(parent)
    return _CircularTelemetryPanel(parent)


class _CircularTelemetryPanel(_SystemStatsPanel):
    def __init__(self, parent: QWidget | None = None, compact: bool = False) -> None:
        super().__init__(parent)
        self._compact = compact
        self._state = _build_placeholder_state("compact" if compact else "circular")

    def apply_state(self, state: SystemStatsDisplayState) -> None:
        self._state = state
        self.update()

    def minimumSizeHint(self):  # type: ignore[override]
        if QSize is object:
            return super().minimumSizeHint()
        return QSize(210, 210) if self._compact else QSize(320, 320)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        if QPainter is object:
            return super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        self._draw_shell(painter, rect)

        if not self._compact:
            header_rect = QRectF(rect.left() + 16, rect.top() + 8, rect.width() - 32, 18)
            self._draw_overline(painter, header_rect)
            self._draw_quad_cluster(
                painter,
                QRectF(rect.left() + 10, rect.top() + 30, rect.width() - 20, rect.height() - 40),
            )
            return

        top_margin = 18 if self._compact else 22
        bottom_nodes = 64 if self._compact else 90
        dial_rect = QRectF(
            rect.left() + 10,
            rect.top() + top_margin,
            rect.width() - 20,
            rect.height() - top_margin - bottom_nodes,
        )
        self._draw_dial(painter, dial_rect)

        self._draw_temperature_nodes(
            painter,
            QRectF(rect.left() + 16, rect.bottom() - bottom_nodes + 12, rect.width() - 32, bottom_nodes - 20),
        )

    def _draw_shell(self, painter: QPainter, rect: QRectF) -> None:
        shell_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        shell_gradient.setColorAt(0.0, QColor(11, 24, 40, 244))
        shell_gradient.setColorAt(0.5, QColor(7, 15, 26, 248))
        shell_gradient.setColorAt(1.0, QColor(4, 8, 14, 252))
        painter.setBrush(shell_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)

    def _draw_overline(self, painter: QPainter, rect: QRectF) -> None:
        font = painter.font()
        font.setPointSize(9)
        if QFont is not object:
            font.setWeight(QFont.Weight.ExtraBold)
        painter.setFont(font)
        painter.setPen(QColor(134, 234, 255, 220))
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._state.overline_text)

    def _draw_dial(self, painter: QPainter, rect: QRectF) -> None:
        self._draw_metric_gauge(
            painter=painter,
            rect=rect,
            metric=self._state.primary_metric,
            secondary_text=f"{self._state.secondary_metric.label}  {self._state.secondary_metric.value_text}",
            compact=self._compact,
        )

    def _draw_metric_gauge(
        self,
        painter: QPainter,
        rect: QRectF,
        metric: DialMetricDisplay,
        secondary_text: str,
        compact: bool,
    ) -> None:
        size = min(rect.width(), rect.height())
        dial_rect = QRectF(0, 0, size, size)
        dial_rect.moveCenter(rect.center())
        center = dial_rect.center()
        outer_radius = dial_rect.width() / 2

        glow = QRadialGradient(center, outer_radius * 1.06)
        glow.setColorAt(0.0, QColor(78, 219, 255, 56))
        glow.setColorAt(0.38, QColor(35, 140, 192, 24))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(dial_rect.adjusted(-14, -14, 14, 14))

        outer_frame = dial_rect.adjusted(8, 8, -8, -8)
        painter.setBrush(QColor(6, 14, 24, 224))
        painter.setPen(QPen(QColor(78, 193, 235, 70), 1.4))
        painter.drawEllipse(outer_frame)

        outer_gradient = QConicalGradient(center, -90)
        outer_gradient.setColorAt(0.0, QColor("#A0FBFF"))
        outer_gradient.setColorAt(0.35, QColor("#50CFFF"))
        outer_gradient.setColorAt(0.7, QColor("#0E5C8E"))
        outer_gradient.setColorAt(1.0, QColor("#A0FBFF"))
        painter.setPen(QPen(outer_gradient, 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(outer_frame, 32 * 16, -284 * 16)

        self._draw_tick_ring(painter, outer_frame)

        primary_arc = outer_frame.adjusted(18, 18, -18, -18)
        self._draw_segmented_progress_arc(
            painter,
            primary_arc,
            metric.normalized_value,
            active_color=_progress_color_for_metric(metric),
            idle_color=QColor(55, 53, 34, 210),
            segments=24 if compact else 30,
            width=8 if compact else 10,
        )

        inner_accent_rect = primary_arc.adjusted(18, 18, -18, -18)
        painter.setPen(QPen(QColor(26, 76, 104, 188), 2))
        painter.drawEllipse(inner_accent_rect)

        center_disc = inner_accent_rect.adjusted(16, 16, -16, -16)
        center_gradient = QRadialGradient(center_disc.center(), center_disc.width() * 0.6)
        center_gradient.setColorAt(0.0, QColor(9, 19, 32, 248))
        center_gradient.setColorAt(1.0, QColor(3, 7, 13, 254))
        painter.setBrush(center_gradient)
        painter.setPen(QPen(QColor(93, 191, 232, 42), 1.2))
        painter.drawEllipse(center_disc)
        self._draw_center_text(painter, center_disc, metric, secondary_text, compact)

    def _draw_tick_ring(self, painter: QPainter, rect: QRectF) -> None:
        center = rect.center()
        outer_radius = rect.width() / 2
        for index in range(21):
            angle = 220 - (280 / 20) * index
            major = index % 5 == 0
            start_radius = outer_radius - (16 if major else 10)
            end_radius = outer_radius - 4
            self._draw_tick(
                painter,
                center=center,
                angle_degrees=angle,
                inner_radius=start_radius,
                outer_radius=end_radius,
                width=2.2 if major else 1.2,
                color=QColor(162, 235, 255, 160 if major else 88),
            )
            if major and not self._compact:
                label_value = str(index * 5)
                label_point = _polar_to_point(center, angle, outer_radius - 28)
                self._draw_numeric_tick(painter, label_point, label_value)

    def _draw_segmented_progress_arc(
        self,
        painter: QPainter,
        rect: QRectF,
        percent: float,
        active_color: QColor,
        idle_color: QColor,
        segments: int,
        width: int,
    ) -> None:
        active_segments = round((percent / 100.0) * segments)
        for segment_index in range(segments):
            start_degrees = 220 - (280 / segments) * segment_index
            span_degrees = (280 / segments) * 0.72
            color = active_color if segment_index < active_segments else idle_color
            painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(rect, int(start_degrees * 16), int(-span_degrees * 16))

    def _draw_center_text(
        self,
        painter: QPainter,
        rect: QRectF,
        metric: DialMetricDisplay,
        secondary_text: str,
        compact: bool,
    ) -> None:
        primary_label_rect = QRectF(rect.left(), rect.top() + rect.height() * 0.16, rect.width(), rect.height() * 0.14)
        primary_value_rect = QRectF(rect.left(), rect.top() + rect.height() * 0.28, rect.width(), rect.height() * 0.28)
        secondary_rect = QRectF(rect.left(), rect.top() + rect.height() * 0.61, rect.width(), rect.height() * 0.20)

        label_font = painter.font()
        label_font.setPointSize(8 if compact else 10)
        if QFont is not object:
            label_font.setWeight(QFont.Weight.Bold)
        painter.setFont(label_font)
        painter.setPen(QColor(139, 241, 255, 208))
        painter.drawText(primary_label_rect, Qt.AlignmentFlag.AlignCenter, metric.label)

        value_font = painter.font()
        value_font.setPointSize(22 if compact else 34)
        if QFont is not object:
            value_font.setWeight(QFont.Weight.ExtraBold)
        painter.setFont(value_font)
        painter.setPen(QColor(171, 252, 255))
        painter.drawText(primary_value_rect, Qt.AlignmentFlag.AlignCenter, metric.value_text)

        secondary_font = painter.font()
        secondary_font.setPointSize(8 if compact else 10)
        if QFont is not object:
            secondary_font.setWeight(QFont.Weight.Bold)
        painter.setFont(secondary_font)
        painter.setPen(QColor(95, 212, 239))
        painter.drawText(secondary_rect, Qt.AlignmentFlag.AlignCenter, secondary_text)

    def _draw_quad_cluster(self, painter: QPainter, rect: QRectF) -> None:
        metrics = self._state.gauge_metrics
        if len(metrics) < 4:
            return

        gap = 12
        cell_width = (rect.width() - gap) / 2
        cell_height = (rect.height() - gap) / 2
        cells = (
            QRectF(rect.left(), rect.top(), cell_width, cell_height),
            QRectF(rect.left() + cell_width + gap, rect.top(), cell_width, cell_height),
            QRectF(rect.left(), rect.top() + cell_height + gap, cell_width, cell_height),
            QRectF(rect.left() + cell_width + gap, rect.top() + cell_height + gap, cell_width, cell_height),
        )
        secondary_lines = (
            metrics[0].detail_text,
            metrics[1].detail_text,
            metrics[2].detail_text,
            metrics[3].detail_text,
        )

        for cell, metric, secondary in zip(cells, metrics, secondary_lines, strict=False):
            self._draw_metric_gauge(painter, cell, metric, secondary, compact=True)

    def _draw_temperature_nodes(self, painter: QPainter, rect: QRectF) -> None:
        nodes = self._state.temperature_nodes
        if not nodes:
            return

        node_diameter = min(rect.height() - 8, rect.width() / (3.6 if self._compact else 4.2))
        spacing = (rect.width() - node_diameter * len(nodes)) / max(1, len(nodes) - 1)
        for index, node in enumerate(nodes):
            node_rect = QRectF(
                rect.left() + index * (node_diameter + spacing),
                rect.top() + 2,
                node_diameter,
                node_diameter,
            )
            self._draw_temperature_node(painter, node_rect, node)

    def _draw_temperature_node(self, painter: QPainter, rect: QRectF, node: TemperatureNodeDisplay) -> None:
        center = rect.center()
        glow = QRadialGradient(center, rect.width() * 0.7)
        accent = QColor(node.accent)
        glow.setColorAt(0.0, QColor(accent.red(), accent.green(), accent.blue(), 54))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect.adjusted(-5, -5, 5, 5))

        shell_gradient = QRadialGradient(rect.center(), rect.width() * 0.62)
        shell_gradient.setColorAt(0.0, QColor(26, 42, 58, 250))
        shell_gradient.setColorAt(0.46, QColor(10, 18, 28, 252))
        shell_gradient.setColorAt(1.0, QColor(4, 8, 13, 255))
        painter.setBrush(shell_gradient)
        painter.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 150), 2))
        painter.drawEllipse(rect)

        highlight = QRectF(rect.left() + rect.width() * 0.18, rect.top() + rect.height() * 0.12, rect.width() * 0.34, rect.height() * 0.24)
        painter.setBrush(QColor(235, 246, 255, 34))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(highlight)

        label_font = painter.font()
        label_font.setPointSize(6 if self._compact else 7)
        if QFont is not object:
            label_font.setWeight(QFont.Weight.Bold)
        painter.setFont(label_font)
        painter.setPen(QColor(154, 224, 240))
        painter.drawText(QRectF(rect.left(), rect.top() + rect.height() * 0.18, rect.width(), rect.height() * 0.16), Qt.AlignmentFlag.AlignCenter, node.label.replace(" TEMP", ""))

        value_font = painter.font()
        value_font.setPointSize(9 if self._compact else 11)
        if QFont is not object:
            value_font.setWeight(QFont.Weight.ExtraBold)
        painter.setFont(value_font)
        painter.setPen(QColor(239, 246, 252))
        painter.drawText(QRectF(rect.left(), rect.top() + rect.height() * 0.42, rect.width(), rect.height() * 0.18), Qt.AlignmentFlag.AlignCenter, node.value_text)

    def _draw_tick(
        self,
        painter: QPainter,
        center: QPointF,
        angle_degrees: float,
        inner_radius: float,
        outer_radius: float,
        width: float,
        color: QColor,
    ) -> None:
        start = _polar_to_point(center, angle_degrees, inner_radius)
        end = _polar_to_point(center, angle_degrees, outer_radius)
        painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(start, end)

    def _draw_numeric_tick(self, painter: QPainter, center: QPointF, text: str) -> None:
        font = painter.font()
        font.setPointSize(7)
        if QFont is not object:
            font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor(119, 196, 225, 142))
        text_rect = QRectF(center.x() - 10, center.y() - 8, 20, 16)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)


class _CompactCircularTelemetryPanel(_CircularTelemetryPanel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, compact=True)


def _build_placeholder_state(layout_variant: str) -> SystemStatsDisplayState:
    return SystemStatsDisplayState(
        layout_variant=layout_variant,
        overline_text="PERFORMANCE STACK",
        primary_metric=_build_dial_metric("CPU", None, "SIGNAL LOST", "#88F5FF"),
        secondary_metric=_build_dial_metric("GPU", None, "STANDBY", "#58D9FF"),
        gauge_metrics=(
            _build_dial_metric("CPU", None, "SIGNAL LOST", "#88F5FF"),
            _build_dial_metric("GPU", None, "STANDBY", "#58D9FF"),
            _build_dial_metric("CPU TEMP", None, "SENSOR OFFLINE", "#9EEBFF"),
            _build_dial_metric("GPU TEMP", None, "CASE --", "#F7D36D"),
        ),
        temperature_nodes=(
            _build_temperature_node("CPU TEMP", None, "#8AF1FF"),
            _build_temperature_node("CASE TEMP", None, "#F9C95F"),
            _build_temperature_node("GPU TEMP", None, "#6FDBFF"),
        ),
    )


def _build_dial_metric(label: str, value: float | None, detail: str, accent: str) -> DialMetricDisplay:
    return DialMetricDisplay(
        label=label,
        value=value,
        value_text=_format_metric_value(label, value),
        detail_text=detail,
        accent=accent,
    )


def _build_temperature_node(label: str, value: float | None, accent: str) -> TemperatureNodeDisplay:
    return TemperatureNodeDisplay(
        label=label,
        value_text=_format_metric_value(label, value),
        detail_text=_temperature_detail(value),
        accent=accent,
    )


def _progress_color_for_metric(metric: DialMetricDisplay) -> QColor:
    if metric.label in {"CPU", "GPU"}:
        return _cpu_load_color(metric.value)
    if metric.label in {"CPU TEMP", "GPU TEMP"}:
        return _temperature_gauge_color(metric.value)
    return QColor("#F7D36D")


def _cpu_load_color(value: float | None) -> QColor:
    if value is None:
        return QColor("#F7D36D")
    if value < 70:
        return QColor("#5BE37A")
    if value < 90:
        return QColor("#F7D36D")
    return QColor("#FF5B5B")


def _temperature_gauge_color(value: float | None) -> QColor:
    if value is None:
        return QColor("#F7D36D")
    if value < 65:
        return QColor("#5BE37A")
    if value < 80:
        return QColor("#F7D36D")
    return QColor("#FF5B5B")


def _polar_to_point(center: QPointF, angle_degrees: float, radius: float) -> QPointF:
    angle_radians = math.radians(angle_degrees - 90)
    return QPointF(
        center.x() + math.cos(angle_radians) * radius,
        center.y() + math.sin(angle_radians) * radius,
    )


def _format_metric_line(label: str, value: float | None) -> str:
    if value is None:
        return f"{label}: unavailable"
    return f"{label}: {value:.1f}%"


def _format_metric_value(label: str, value: float | None) -> str:
    if label in {"CPU", "GPU", "RAM"}:
        if value is None:
            return "--"
        return f"{value:.0f}%"
    if "TEMP" in label:
        if value is None:
            return "--"
        return f"{value:.0f}C"
    if "CLK" in label:
        if value is None:
            return "--"
        return f"{value:.1f}"
    if value is None:
        return "--"
    return f"{value:.1f}"


def _percent_status(value: float | None) -> str:
    if value is None:
        return "SIGNAL LOST"
    if value >= 85:
        return "SATURATED"
    if value >= 60:
        return "HEAVY LOAD"
    if value >= 30:
        return "ACTIVE"
    return "STABLE"


def _status_detail(value: float | None) -> str:
    if value is None:
        return "STANDBY"
    return _percent_status(value)


def _temperature_detail(value: float | None) -> str:
    if value is None:
        return "SENSOR OFFLINE"
    if value >= 80:
        return "HOT ZONE"
    if value >= 65:
        return "WARM"
    return "NOMINAL"


def _case_temperature_detail(value: float | None) -> str:
    if value is None:
        return "CASE --"
    return f"CASE {value:.0f}C"


def _is_relevant_gpu_counter_path(path: str) -> bool:
    normalized = path.lower()
    if "engtype_" not in normalized:
        return False
    return any(
        engine in normalized
        for engine in (
            "engtype_3d",
            "engtype_compute",
            "engtype_cuda",
            "engtype_copy",
            "engtype_videodecode",
            "engtype_videoencode",
        )
    )


def _coerce_optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def _get_pdh_fmt_countervalue_double_type():
    class PdhFmtCounterValueDouble(ctypes.Structure):
        _fields_ = [
            ("CStatus", ctypes.c_ulong),
            ("doubleValue", ctypes.c_double),
        ]

    return PdhFmtCounterValueDouble


def _filetime_to_int(value) -> int:
    return (value.dwHighDateTime << 32) | value.dwLowDateTime


_PDH_FMT_DOUBLE = 0x00000200
_PDH_MORE_DATA = 0x800007D2
