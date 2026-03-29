from __future__ import annotations

import configparser
import ctypes
import ctypes.wintypes
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

HWINFO_SHARED_MEM_PATH = "Global\\HWiNFO_SENS_SM2"
HWINFO_HEADER_MAGIC = 0x53695748
WM_CLOSE = 0x0010


def _build_windows_subprocess_kwargs() -> dict[str, object]:
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}


@dataclass(frozen=True)
class HWiNFOSensorEntry:
    sensor_name: str
    label: str
    unit: str
    value: float


@dataclass(frozen=True)
class HWiNFOMetrics:
    gpu_percent: float | None
    cpu_temp_c: float | None
    case_temp_c: float | None
    gpu_temp_c: float | None


class _HWiNFOHeader(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("magic", ctypes.c_uint32),
        ("version", ctypes.c_uint32),
        ("version2", ctypes.c_uint32),
        ("last_update", ctypes.c_int64),
        ("sensor_section_offset", ctypes.c_uint32),
        ("sensor_element_size", ctypes.c_uint32),
        ("sensor_element_count", ctypes.c_uint32),
        ("entry_section_offset", ctypes.c_uint32),
        ("entry_element_size", ctypes.c_uint32),
        ("entry_element_count", ctypes.c_uint32),
    ]


class _HWiNFOSensor(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("instance", ctypes.c_uint32),
        ("name_original", ctypes.c_char * 128),
        ("name_user", ctypes.c_char * 128),
    ]


class _HWiNFOEntry(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("type", ctypes.c_uint32),
        ("sensor_index", ctypes.c_uint32),
        ("id", ctypes.c_uint32),
        ("name_original", ctypes.c_char * 128),
        ("name_user", ctypes.c_char * 128),
        ("unit", ctypes.c_char * 16),
        ("value", ctypes.c_double),
        ("value_min", ctypes.c_double),
        ("value_max", ctypes.c_double),
        ("value_avg", ctypes.c_double),
    ]


class HWiNFOBridge:
    def __init__(
        self,
        source_exe_path: Path | None = None,
        managed_root: Path | None = None,
    ) -> None:
        self._source_exe_path = source_exe_path or Path(r"C:\Program Files\HWiNFO64\HWiNFO64.EXE")
        default_root = Path.cwd() / ".proxdeck" / "tools" / "HWiNFO64"
        self._managed_root = managed_root or default_root
        self._exe_path = self._managed_root / "HWiNFO64.EXE"
        self._ini_path = self._managed_root / "HWiNFO64.INI"
        self._last_metrics_at = 0.0
        self._cached_metrics = HWiNFOMetrics(gpu_percent=None, cpu_temp_c=None, case_temp_c=None, gpu_temp_c=None)
        self._restart_attempted = False
        self._start_attempted = False

    def read_metrics(self) -> HWiNFOMetrics:
        now = time.monotonic()
        if now - self._last_metrics_at < 3.0:
            return self._cached_metrics

        self._last_metrics_at = now
        self._ensure_hwinfo_ready()

        entries = self._read_entries()
        if not entries:
            return self._cached_metrics

        self._cached_metrics = HWiNFOMetrics(
            gpu_percent=_select_gpu_percent(entries),
            cpu_temp_c=_select_cpu_temp(entries),
            case_temp_c=_select_case_temp(entries),
            gpu_temp_c=_select_gpu_temp(entries),
        )
        return self._cached_metrics

    def _ensure_hwinfo_ready(self) -> None:
        if not self._ensure_managed_install():
            return

        self._ensure_ini_flags()
        if self._shared_memory_available():
            return

        if not self._is_hwinfo_running():
            self._start_hwinfo()
            return

        if self._restart_attempted:
            return

        self._restart_attempted = True
        self._close_hwinfo_window()
        time.sleep(1.5)
        self._start_hwinfo()

    def _ensure_ini_flags(self) -> None:
        self._ini_path.parent.mkdir(parents=True, exist_ok=True)
        config = configparser.ConfigParser()
        config.optionxform = str
        if self._ini_path.exists():
            config.read(self._ini_path, encoding="utf-8")
        if "Settings" not in config:
            config["Settings"] = {}

        settings = config["Settings"]
        settings["SensorsSM"] = "1"
        settings["SensorsOnly"] = "1"
        settings["MinimalizeSensors"] = "1"

        try:
            with self._ini_path.open("w", encoding="utf-8") as handle:
                config.write(handle)
        except PermissionError:
            return

    def _ensure_managed_install(self) -> bool:
        if not self._exe_path.exists():
            if not self._source_exe_path.exists():
                return False
            self._managed_root.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self._source_exe_path, self._exe_path)
            return True

        if self._source_exe_path.exists() and self._source_exe_path.stat().st_mtime > self._exe_path.stat().st_mtime:
            self._managed_root.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self._source_exe_path, self._exe_path)
        return True

    def _shared_memory_available(self) -> bool:
        handle = ctypes.windll.kernel32.OpenFileMappingW(0x0004, False, HWINFO_SHARED_MEM_PATH)
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True

    def _is_hwinfo_running(self) -> bool:
        try:
            completed = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq HWiNFO64.EXE", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=3.0,
                check=False,
                **_build_windows_subprocess_kwargs(),
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return "HWiNFO64.EXE" in completed.stdout

    def _start_hwinfo(self) -> None:
        if self._start_attempted and self._shared_memory_available():
            return
        self._start_attempted = True
        try:
            subprocess.Popen(
                [str(self._exe_path)],
                cwd=str(self._exe_path.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **_build_windows_subprocess_kwargs(),
            )
        except OSError:
            return

        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            if self._shared_memory_available():
                return
            time.sleep(0.5)

    def _close_hwinfo_window(self) -> None:
        user32 = ctypes.windll.user32

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        def enum_windows_proc(hwnd, _lparam):
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value
            if "HWiNFO" in title:
                user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            return True

        user32.EnumWindows(enum_windows_proc, 0)

    def _read_entries(self) -> list[HWiNFOSensorEntry]:
        kernel32 = ctypes.windll.kernel32
        kernel32.OpenFileMappingW.argtypes = [
            ctypes.wintypes.DWORD,
            ctypes.wintypes.BOOL,
            ctypes.wintypes.LPCWSTR,
        ]
        kernel32.OpenFileMappingW.restype = ctypes.wintypes.HANDLE
        kernel32.MapViewOfFile.argtypes = [
            ctypes.wintypes.HANDLE,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD,
            ctypes.c_size_t,
        ]
        kernel32.MapViewOfFile.restype = ctypes.c_void_p

        handle = kernel32.OpenFileMappingW(0x0004, False, HWINFO_SHARED_MEM_PATH)
        if not handle:
            return []

        pointer = kernel32.MapViewOfFile(handle, 0x0004, 0, 0, 0)
        if not pointer:
            kernel32.CloseHandle(handle)
            return []

        try:
            header = _HWiNFOHeader.from_address(pointer)
            if header.magic != HWINFO_HEADER_MAGIC:
                return []

            sensors: dict[int, str] = {}
            sensor_base = pointer + header.sensor_section_offset
            for index in range(header.sensor_element_count):
                sensor_addr = sensor_base + (index * header.sensor_element_size)
                sensor = _HWiNFOSensor.from_address(sensor_addr)
                sensors[index] = _decode_hwinfo_text(sensor.name_user) or _decode_hwinfo_text(sensor.name_original)

            entries: list[HWiNFOSensorEntry] = []
            entry_base = pointer + header.entry_section_offset
            for index in range(header.entry_element_count):
                entry_addr = entry_base + (index * header.entry_element_size)
                entry = _HWiNFOEntry.from_address(entry_addr)
                sensor_name = sensors.get(entry.sensor_index, "")
                label = _decode_hwinfo_text(entry.name_user) or _decode_hwinfo_text(entry.name_original)
                unit = _decode_hwinfo_text(entry.unit)
                entries.append(
                    HWiNFOSensorEntry(
                        sensor_name=sensor_name,
                        label=label,
                        unit=unit,
                        value=float(entry.value),
                    )
                )
            return entries
        finally:
            kernel32.UnmapViewOfFile(ctypes.c_void_p(pointer))
            kernel32.CloseHandle(handle)


def _decode_hwinfo_text(value: bytes) -> str:
    return value.decode("utf-8", errors="ignore").strip("\x00").strip()


def _select_cpu_temp(entries: list[HWiNFOSensorEntry]) -> float | None:
    candidates = [
        entry
        for entry in entries
        if _is_temperature_unit(entry.unit) and entry.value > 0 and _is_cpu_temp_candidate(entry)
    ]
    if not candidates:
        return None
    candidates.sort(key=_cpu_temp_score, reverse=True)
    return round(candidates[0].value, 1)


def _is_cpu_temp_candidate(entry: HWiNFOSensorEntry) -> bool:
    label = entry.label.lower()
    sensor = entry.sensor_name.lower()
    if "gpu" in label or "gpu" in sensor:
        return False
    return any(
        token in label or token in sensor
        for token in ("cpu", "package", "tctl", "tdie", "core", "ryzen")
    )


def _cpu_temp_score(entry: HWiNFOSensorEntry) -> int:
    label = entry.label.lower()
    sensor = entry.sensor_name.lower()
    score = 0
    if "package" in label:
        score += 100
    if "tctl" in label or "tdie" in label:
        score += 95
    if label == "cpu":
        score += 90
    if "cpu" in label:
        score += 80
    if "core" in label:
        score += 40
    if "gigabyte" in sensor or "x570" in sensor:
        score += 30
    if "ryzen" in sensor:
        score += 20
    return score


def _select_case_temp(entries: list[HWiNFOSensorEntry]) -> float | None:
    candidates = [
        entry
        for entry in entries
        if _is_temperature_unit(entry.unit) and entry.value > 0 and _is_case_temp_candidate(entry)
    ]
    if not candidates:
        return None
    candidates.sort(key=_case_temp_score, reverse=True)
    return round(candidates[0].value, 1)


def _is_case_temp_candidate(entry: HWiNFOSensorEntry) -> bool:
    label = entry.label.lower()
    sensor = entry.sensor_name.lower()
    if any(token in label for token in ("cpu", "gpu", "hot spot", "vrm")):
        return False
    return any(
        token in label or token in sensor
        for token in ("system", "motherboard", "board", "chipset", "pch", "case")
    )


def _case_temp_score(entry: HWiNFOSensorEntry) -> int:
    label = entry.label.lower()
    sensor = entry.sensor_name.lower()
    score = 0
    if "case" in label:
        score += 100
    if "system" in label:
        score += 90
    if "motherboard" in label or "board" in label:
        score += 80
    if "chipset" in label or "pch" in label:
        score += 70
    if "gigabyte" in sensor or "x570" in sensor:
        score += 20
    return score


def _select_gpu_temp(entries: list[HWiNFOSensorEntry]) -> float | None:
    candidates = [
        entry
        for entry in entries
        if _is_temperature_unit(entry.unit) and entry.value > 0 and _is_gpu_temp_candidate(entry)
    ]
    if not candidates:
        return None
    candidates.sort(key=_gpu_temp_score, reverse=True)
    return round(candidates[0].value, 1)


def _select_gpu_percent(entries: list[HWiNFOSensorEntry]) -> float | None:
    candidates = [
        entry
        for entry in entries
        if entry.unit == "%" and entry.value >= 0 and _is_gpu_percent_candidate(entry)
    ]
    if not candidates:
        return None
    candidates.sort(key=_gpu_percent_score, reverse=True)
    return round(min(100.0, max(0.0, candidates[0].value)), 1)


def _is_gpu_temp_candidate(entry: HWiNFOSensorEntry) -> bool:
    label = entry.label.lower()
    sensor = entry.sensor_name.lower()
    return "gpu" in label or "nvidia" in sensor


def _is_gpu_percent_candidate(entry: HWiNFOSensorEntry) -> bool:
    label = entry.label.lower()
    sensor = entry.sensor_name.lower()
    if "gpu" not in label and "gpu" not in sensor and "nvidia" not in sensor:
        return False
    blocked_tokens = (
        "fan",
        "ventilator",
        "memory",
        "bus",
        "video",
        "tdp",
        "power",
        "thermal",
        "hotspot",
        "hot spot",
    )
    return not any(token in label for token in blocked_tokens)


def _gpu_temp_score(entry: HWiNFOSensorEntry) -> int:
    label = entry.label.lower()
    score = 0
    if label == "gpu core":
        score += 100
    if "gpu temperature" in label:
        score += 95
    if "hot spot" in label:
        score += 60
    if "gpu" in label:
        score += 40
    return score


def _gpu_percent_score(entry: HWiNFOSensorEntry) -> int:
    label = entry.label.lower()
    score = 0
    if "core load" in label or "kernbelasting" in label:
        score += 120
    if "d3d" in label:
        score += 110
    if "gpu load" in label:
        score += 100
    if "gpu" in label:
        score += 40
    return score


def _is_temperature_unit(unit: str) -> bool:
    normalized = unit.strip().lower()
    return normalized in {"c", "°c"} or normalized.endswith("c")
