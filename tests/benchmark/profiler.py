"""
tests.benchmark.profiler
~~~~~~~~~~~~~~~~~~~~~~~~
Narzędzie do precyzyjnego pomiaru alokacji pamięci, profilowania zużycia CPU,
wykrywania wycieków pamięci (memory leaks) oraz monitorowania VRAM i utylizacji GPU.
Zgodne z Czystą Architekturą, ścisłe typowanie bez Any (Python 3.14+).
"""

import ctypes
import gc
import os
import shutil
import subprocess
import sys
import time
import tracemalloc
from ctypes import wintypes
from dataclasses import dataclass
from typing import Callable, Optional


# --- Struktury Windows API do pomiaru Working Set (RSS) ---
class _PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def get_process_working_set_bytes() -> int:
    """Zwraca fizyczny rozmiar pamięci RAM procesu (Working Set / RSS) w bajtach."""
    if sys.platform == "win32":
        try:
            psapi = ctypes.WinDLL("psapi")
            kernel32 = ctypes.WinDLL("kernel32")
            get_mem = psapi.GetProcessMemoryInfo
            get_mem.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
            get_mem.restype = wintypes.BOOL

            counters = _PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(_PROCESS_MEMORY_COUNTERS)
            success = get_mem(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
            if success:
                return int(counters.WorkingSetSize)
        except Exception:
            pass
    return 0


@dataclass(frozen=True)
class GpuMetrics:
    """Metryki zasobów akceleratora graficznego GPU."""
    name: str
    total_vram_bytes: int
    used_vram_bytes: int
    free_vram_bytes: int
    utilization_pct: float

    @property
    def free_vram_mb(self) -> float:
        return self.free_vram_bytes / (1024 * 1024)

    @property
    def used_vram_mb(self) -> float:
        return self.used_vram_bytes / (1024 * 1024)

    @property
    def total_vram_mb(self) -> float:
        return self.total_vram_bytes / (1024 * 1024)


def get_gpu_metrics() -> Optional[GpuMetrics]:
    """
    Odpytuje kartę graficzną NVIDIA o zużycie pamięci VRAM oraz utylizację rdzeni CUDA.
    Zwraca None, jeśli brak akceleratora GPU lub narzędzia nvidia-smi.
    """
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return None

    try:
        cmd = [
            nvidia_smi,
            "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=3.0)
        output = result.stdout.strip()
        if not output:
            return None

        # Format: Name, total_mb, used_mb, free_mb, util_pct
        parts = [p.strip() for p in output.split(",")]
        if len(parts) >= 5:
            name = parts[0]
            total_mb = float(parts[1])
            used_mb = float(parts[2])
            free_mb = float(parts[3])
            util_pct = float(parts[4])
            return GpuMetrics(
                name=name,
                total_vram_bytes=int(total_mb * 1024 * 1024),
                used_vram_bytes=int(used_mb * 1024 * 1024),
                free_vram_bytes=int(free_mb * 1024 * 1024),
                utilization_pct=util_pct,
            )
    except Exception:
        pass
    return None


def format_bytes(num_bytes: int | float) -> str:
    """Formatuje liczbę bajtów do czytelnej postaci (B, KB, MB, GB)."""
    val = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(val) < 1024.0 or unit == "GB":
            return f"{val:.2f} {unit}"
        val /= 1024.0
    return f"{val:.2f} GB"


@dataclass(frozen=True)
class BenchmarkResult:
    """Kompletny raport z wykonanego testu obciążeniowego i pomiaru zasobów."""
    name: str
    iterations: int
    duration_sec: float
    cpu_time_sec: float
    cpu_utilization_pct: float
    initial_heap_bytes: int
    final_heap_bytes: int
    heap_delta_bytes: int
    peak_heap_bytes: int
    initial_working_set_bytes: int
    final_working_set_bytes: int
    working_set_delta_bytes: int
    initial_gpu_vram_bytes: Optional[int]
    final_gpu_vram_bytes: Optional[int]
    gpu_vram_delta_bytes: Optional[int]
    gpu_utilization_pct: Optional[float]
    gpu_name: Optional[str]
    leak_detected: bool
    memory_norm_exceeded: bool
    top_allocations: tuple[str, ...]

    def summary(self) -> str:
        """Generuje sformatowane podsumowanie tekstowe metryk."""
        leak_str = "❌ WYKRYTO WYCIEK!" if self.leak_detected else "✅ BRAK WYCIEKÓW"
        norm_str = "❌ PRZEKROCZONO NORMĘ!" if self.memory_norm_exceeded else "✅ W NORMIE"
        lines = [
            f"=== Benchmark: {self.name} ({self.iterations} powtórzeń) ===",
            f"  ⏱️  Czas trwania:      {self.duration_sec:.4f} s (CPU: {self.cpu_time_sec:.4f} s | {self.cpu_utilization_pct:.1f}% CPU)",
            f"  🧠 Python Heap:       Początek: {format_bytes(self.initial_heap_bytes)} | Koniec: {format_bytes(self.final_heap_bytes)} | Delta: {format_bytes(self.heap_delta_bytes)}",
            f"  📈 Szczyt alokacji:   {format_bytes(self.peak_heap_bytes)}",
            f"  🏢 OS Working Set:    {format_bytes(self.initial_working_set_bytes)} -> {format_bytes(self.final_working_set_bytes)} (Delta: {format_bytes(self.working_set_delta_bytes)})",
            f"  🛡️  Stan pamięci:      {norm_str} | {leak_str}",
        ]
        if self.gpu_name:
            vram_str = f"Delta VRAM: {format_bytes(self.gpu_vram_delta_bytes or 0)}"
            lines.append(f"  🎮 GPU ({self.gpu_name}): {vram_str} | Utylizacja: {self.gpu_utilization_pct or 0.0:.1f}%")
        if self.top_allocations:
            lines.append("  🔍 Największe alokacje:")
            for item in self.top_allocations[:3]:
                lines.append(f"     * {item}")
        return "\n".join(lines)


class ResourceProfiler:
    """
    Zaawansowany menedżer profilowania alokacji pamięci, wycieków pamięci,
    zużycia CPU i monitoringu GPU.
    """

    def __init__(
        self,
        name: str,
        max_allowed_heap_bytes: int = 100 * 1024 * 1024,
        max_allowed_leak_growth_bytes: int = 2 * 1024 * 1024,
    ) -> None:
        self.name = name
        self.max_allowed_heap_bytes = max_allowed_heap_bytes
        self.max_allowed_leak_growth_bytes = max_allowed_leak_growth_bytes

    def run(self, fn: Callable[[], object], iterations: int = 1, warmup: int = 1) -> BenchmarkResult:
        """
        Wykonuje funkcję wskazaną liczbę razy, monitorując alokacje pamięci,
        wykrywając potencjalne wycieki pamięci oraz mierząc czas CPU i stan GPU.
        """
        # Faza rozgrzewki (warmup)
        for _ in range(warmup):
            fn()
        gc.collect()

        # Inicjalizacja tracemalloc i odczyt stanu początkowego
        was_tracing = tracemalloc.is_tracing()
        if not was_tracing:
            tracemalloc.start()
        tracemalloc.clear_traces()

        initial_snapshot = tracemalloc.take_snapshot()
        initial_heap_current, _ = tracemalloc.get_traced_memory()
        initial_ws = get_process_working_set_bytes()
        initial_gpu = get_gpu_metrics()

        start_wall_time = time.perf_counter()
        start_cpu_time = time.process_time()

        # Faza testowa
        for _ in range(iterations):
            fn()

        end_cpu_time = time.process_time()
        end_wall_time = time.perf_counter()

        # Zbieranie śmieci przed pomiarem wycieków (nieodzyskiwalne obiekty = wyciek)
        gc.collect()

        final_snapshot = tracemalloc.take_snapshot()
        final_heap_current, peak_heap = tracemalloc.get_traced_memory()
        final_ws = get_process_working_set_bytes()
        final_gpu = get_gpu_metrics()

        if not was_tracing:
            tracemalloc.stop()

        # Obliczenia CPU
        duration_sec = max(end_wall_time - start_wall_time, 1e-9)
        cpu_time_sec = end_cpu_time - start_cpu_time
        cpu_utilization_pct = min((cpu_time_sec / duration_sec) * 100.0, 100.0 * (os.cpu_count() or 1))

        # Obliczenia pamięci
        heap_delta = final_heap_current - initial_heap_current
        ws_delta = final_ws - initial_ws

        # Sprawdzenie wycieków pamięci (diff snapshotów)
        diff_stats = final_snapshot.compare_to(initial_snapshot, "lineno")
        top_alloc_lines: list[str] = [str(stat) for stat in diff_stats[:5]]
        cumulative_growth = sum(stat.size_diff for stat in diff_stats if stat.size_diff > 0)
        leak_detected = cumulative_growth > self.max_allowed_leak_growth_bytes

        # Sprawdzenie przekroczenia normy pamięci
        memory_norm_exceeded = peak_heap > self.max_allowed_heap_bytes

        # Obliczenia GPU
        gpu_name: Optional[str] = None
        initial_vram: Optional[int] = None
        final_vram: Optional[int] = None
        vram_delta: Optional[int] = None
        gpu_util: Optional[float] = None

        if initial_gpu and final_gpu:
            gpu_name = final_gpu.name
            initial_vram = initial_gpu.used_vram_bytes
            final_vram = final_gpu.used_vram_bytes
            vram_delta = final_vram - initial_vram
            gpu_util = final_gpu.utilization_pct

        return BenchmarkResult(
            name=self.name,
            iterations=iterations,
            duration_sec=duration_sec,
            cpu_time_sec=cpu_time_sec,
            cpu_utilization_pct=cpu_utilization_pct,
            initial_heap_bytes=initial_heap_current,
            final_heap_bytes=final_heap_current,
            heap_delta_bytes=heap_delta,
            peak_heap_bytes=peak_heap,
            initial_working_set_bytes=initial_ws,
            final_working_set_bytes=final_ws,
            working_set_delta_bytes=ws_delta,
            initial_gpu_vram_bytes=initial_vram,
            final_gpu_vram_bytes=final_vram,
            gpu_vram_delta_bytes=vram_delta,
            gpu_utilization_pct=gpu_util,
            gpu_name=gpu_name,
            leak_detected=leak_detected,
            memory_norm_exceeded=memory_norm_exceeded,
            top_allocations=tuple(top_alloc_lines),
        )
