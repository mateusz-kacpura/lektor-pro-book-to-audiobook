"""Performance and throughput benchmark runner for TTS synthesis and text normalization."""

import os
import sys
import time
from pathlib import Path
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Implementation note: see the surrounding code for the behavior described here.
if sys.platform == "win32":
    try:
        reconfig = getattr(sys.stdout, "reconfigure", None)
        if callable(reconfig):
            reconfig(encoding="utf-8", errors="replace")
    except Exception:
        pass

import numpy as np
from fastapi.testclient import TestClient

from lektor.adapters.audio.cleaner import SileroAudioCleaner
from lektor.adapters.audio.stitcher import NumpyAudioStitcher
from lektor.infrastructure.gui_app import app
from lektor.domain.audio_models import make_audio_buffer
from lektor.domain.normalization import TextNormalizationService
from tests.benchmark.profiler import (
    BenchmarkResult,
    ResourceProfiler,
    format_bytes,
    get_gpu_metrics,
    get_process_working_set_bytes,
)


def print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(f"  đźš€ {title}")
    print("=" * 80)


def print_system_info() -> None:
    print_header("DIAGNOSTYKA SPRZÄTOWA I ĹšRODOWISKOWA (HARDWARE & SYSTEM)")
    print(f"  đź’» System operacyjny:    {sys.platform} ({os.name})")
    print(f"  đźŤ Wersja Pythona:       {sys.version.split()[0]}")
    print(f"  đź§  DostÄ™pne rdzenie CPU: {os.cpu_count() or 'N/A'}")
    ram_bytes = get_process_working_set_bytes()
    print(f"  đźŹ˘ BieĹĽÄ…cy RAM (RSS):    {format_bytes(ram_bytes)}")

    gpu = get_gpu_metrics()
    if gpu:
        print(f"  đźŽ® Dedykowane GPU:       {gpu.name}")
        print(f"  đź’ľ PamiÄ™Ä‡ VRAM:          {gpu.used_vram_mb:.1f} MB / {gpu.total_vram_mb:.1f} MB (Wolne: {gpu.free_vram_mb:.1f} MB)")
        print(f"  âšˇ Utylizacja CUDA:      {gpu.utilization_pct:.1f}%")
        if gpu.free_vram_mb < 2000.0:
            print("  âš ď¸Ź  OSTRZEĹ»ENIE: Wolna pamiÄ™Ä‡ VRAM jest poniĹĽej zalecanej normy 2000 MB!")
        else:
            print("  âś… Zasoby VRAM w peĹ‚nej normie dla modeli AI Chatterbox & Qwen2.5-VL")
    else:
        print("  â„ąď¸Ź  GPU: Brak dedykowanego akceleratora NVIDIA / tryb CPU")


def run_all_benchmarks() -> Sequence[BenchmarkResult]:
    results: list[BenchmarkResult] = []

    # 1. Text normalization
    print("\n[1/4] đź“– Uruchamianie benchmarku: Normalizacja tekstu technicznego...")
    normalizer = TextNormalizationService()
    sample_text = """
# Cloud Native Go v2.0
Wzorzec Circuit Breaker zapobiega przeciÄ…ĹĽeniu.
Listing:
```go
func handle(w http.ResponseWriter, r *http.Request) {
    if err != nil {
        return
    }
}
```
ZĹ‚oĹĽonoĹ›Ä‡ O(n log n). Serwery Kubernetes k8s obsĹ‚uĹĽyĹ‚y 100% ruchu.
""" * 40

    norm_profiler = ResourceProfiler("Normalizacja tekstu (Domain Layer)", max_allowed_heap_bytes=25 * 1024 * 1024)
    res_norm = norm_profiler.run(
        lambda: normalizer.normalize(sample_text),
        iterations=10,
        warmup=2,
    )
    results.append(res_norm)
    print(f"     -> Czas: {res_norm.duration_sec:.3f}s | Szczyt RAM: {format_bytes(res_norm.peak_heap_bytes)} | Leak: {'NIE' if not res_norm.leak_detected else 'TAK'}")

    # Implementation note: see the surrounding code for the behavior described here.
    print("\n[2/4] đźŽµ Uruchamianie benchmarku: ĹÄ…czenie buforĂłw audio (NumPy)...")
    stitcher = NumpyAudioStitcher(sample_rate=24000)
    cleaner = SileroAudioCleaner(sample_rate=24000)
    segments = [
        (make_audio_buffer(np.sin(np.linspace(0, 1.0, 24000, dtype=np.float32))), 200)
        for _ in range(15)
    ]

    stitch_profiler = ResourceProfiler("ĹÄ…czenie i czyszczenie audio (NumPy)", max_allowed_heap_bytes=30 * 1024 * 1024)

    def audio_work() -> None:
        stitched = stitcher.stitch_segments(segments)
        cleaner.clean_tail(stitched, sample_rate=24000)

    res_stitch = stitch_profiler.run(audio_work, iterations=15, warmup=2)
    results.append(res_stitch)
    print(f"     -> Czas: {res_stitch.duration_sec:.3f}s | Szczyt RAM: {format_bytes(res_stitch.peak_heap_bytes)} | Leak: {'NIE' if not res_stitch.leak_detected else 'TAK'}")

    # 3. Web GUI Throughput
    print("\n[3/4] đźŚ Uruchamianie benchmarku: PrzepustowoĹ›Ä‡ Web GUI (FastAPI)...")
    client = TestClient(app)
    gui_profiler = ResourceProfiler("PrzepustowoĹ›Ä‡ Web GUI (50 zapytaĹ„)", max_allowed_heap_bytes=25 * 1024 * 1024)
    res_gui = gui_profiler.run(lambda: client.get("/api/status"), iterations=50, warmup=5)
    results.append(res_gui)
    print(f"     -> Czas: {res_gui.duration_sec:.3f}s | Ĺšr: {(res_gui.duration_sec / 50)*1000:.2f}ms/zapytanie | Leak: {'NIE' if not res_gui.leak_detected else 'TAK'}")

    # 4. Check acceleration and VRAM
    print("\n[4/4] âšˇ Uruchamianie benchmarku: StabilnoĹ›Ä‡ alokacji i zasoby sprzÄ™towe...")
    gpu_profiler = ResourceProfiler("Diagnostyka zasobĂłw VRAM i CPU", max_allowed_heap_bytes=10 * 1024 * 1024)
    res_gpu = gpu_profiler.run(lambda: time.sleep(0.01), iterations=5, warmup=1)
    results.append(res_gpu)
    print(f"     -> Pomiar zakoĹ„czony. VRAM: {res_gpu.gpu_name or 'Tryb CPU'}")

    return results


def print_summary_table(results: Sequence[BenchmarkResult]) -> bool:
    print_header("PODSUMOWANIE BENCHMARKĂ“W I ZUĹ»YCIA ZASOBĂ“W")
    header_fmt = "{:<32} | {:<10} | {:<8} | {:<12} | {:<10} | {:<10}"
    print(header_fmt.format("Nazwa testu", "Czas", "CPU %", "Szczyt Heap", "Wycieki", "Norma"))
    print("-" * 92)

    has_failures = False
    for r in results:
        leak_txt = "âś… BRAK" if not r.leak_detected else "âťŚ WYCIEK!"
        norm_txt = "âś… OK" if not r.memory_norm_exceeded else "âťŚ PRZEKROCZONA"
        if r.leak_detected or r.memory_norm_exceeded:
            has_failures = True
        print(
            header_fmt.format(
                r.name[:32],
                f"{r.duration_sec:.3f}s",
                f"{r.cpu_utilization_pct:.1f}%",
                format_bytes(r.peak_heap_bytes),
                leak_txt,
                norm_txt,
            )
        )

    print("-" * 92)
    if has_failures:
        print("  âťŚ UWAGA: NiektĂłre testy wykryĹ‚y wyciek pamiÄ™ci lub przekroczyĹ‚y zdefiniowanÄ… normÄ™!")
    else:
        print("  đźŽ‰ Wszystkie testy wydajnoĹ›ciowe zakoĹ„czone sukcesem. Zasoby pamiÄ™ci i CPU w normie, brak wyciekĂłw!")
    print("=" * 80 + "\n")
    return not has_failures


def main() -> None:
    print_system_info()
    results = run_all_benchmarks()
    success = print_summary_table(results)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
