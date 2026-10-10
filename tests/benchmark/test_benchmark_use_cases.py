"""
tests.benchmark.test_benchmark_use_cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Testy benchmarkowe przypadków użycia (Use Cases Layer) oraz orkiestracji syntezy mowy.
Śledzenie alokacji pamięci na stronę, wykrywanie wycieków i profilowanie CPU.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from lektor.adapters.audio.stitcher import NumpyAudioStitcher
from lektor.adapters.storage.file_repository import FileSystemPageRepository
from lektor.adapters.tts.mock_engine import MockTTSEngine
from lektor.application.dtos import SynthesizePageCommand
from lektor.application.use_cases.synthesize_page import SynthesizePageUseCase
from lektor.domain.normalization import TextNormalizationService
from tests.benchmark.profiler import ResourceProfiler


class TestBenchmarkUseCases(unittest.TestCase):
    """Testy obciążeniowe i pamięciowe przepływu syntezy mowy w warstwie aplikacji."""

    temp_dir: Path
    page_repo: FileSystemPageRepository
    use_case: SynthesizePageUseCase
    test_page_path: Path
    out_dir: Path

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="lektor_benchmark_uc_"))
        pages_dir = self.temp_dir / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        self.out_dir = self.temp_dir / "audio_out"
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.page_repo = FileSystemPageRepository()
        self.use_case = SynthesizePageUseCase(
            tts_engine=MockTTSEngine(),
            audio_stitcher=NumpyAudioStitcher(),
            page_repository=self.page_repo,
            normalization_service=TextNormalizationService(),
        )

        self.test_page_path = pages_dir / "page_001.md"
        self.test_page_path.write_text(
            """# Strona 1: Wzorzec Circuit Breaker w Go
W systemach rozproszonych awaria pojedynczej usługi może wywołać lawinę błędów kaskadowych.
Wzorzec Circuit Breaker zapobiega ponawianiu zapytań do niedostępnego serwisu.
Implementacja bazuje na maszynie stanów: Closed, Open i Half-Open.
```go
package main

func query() error {
    return nil
}
```
""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_benchmark_synthesize_page_allocation_norm(self) -> None:
        """Weryfikuje, czy alokacja pamięci dla pełnej syntezy strony mieści się w normie."""
        profiler = ResourceProfiler(
            name="Pełna synteza strony Use Case (Mock Engine)",
            max_allowed_heap_bytes=20 * 1024 * 1024,  # Norma: max 20 MB heap per strona
            max_allowed_leak_growth_bytes=1024 * 1024,
        )

        cmd = SynthesizePageCommand(
            markdown_path=self.test_page_path,
            output_dir=self.out_dir,
            audio_format="wav",
        )

        def run_use_case() -> None:
            result = self.use_case.execute(cmd)
            self.assertTrue(result.audio_path.exists())

        res = profiler.run(run_use_case, iterations=1, warmup=1)

        self.assertFalse(res.memory_norm_exceeded, f"Przekroczono limit pamięci heap: {res.peak_heap_bytes} B")
        self.assertFalse(res.leak_detected, "Wykryto wyciek pamięci podczas syntezy!")
        self.assertLess(res.duration_sec, 2.0, "Synteza pojedynczej strony trwała zbyt długo!")

    def test_benchmark_synthesize_page_memory_leak(self) -> None:
        """Weryfikuje brak wycieków pamięci przy 20 powtórzeniach syntezy strony."""
        profiler = ResourceProfiler(
            name="Wykrywanie wycieków pamięci: SynthesizePageUseCase (20 cykli)",
            max_allowed_heap_bytes=25 * 1024 * 1024,
            max_allowed_leak_growth_bytes=1536 * 1024,  # Norma wycieku: poniżej 1.5 MB po 20 cyklach
        )

        cmd = SynthesizePageCommand(
            markdown_path=self.test_page_path,
            output_dir=self.out_dir,
            audio_format="wav",
        )

        def run_loop() -> None:
            self.use_case.execute(cmd)

        res = profiler.run(run_loop, iterations=20, warmup=2)

        self.assertFalse(
            res.leak_detected,
            f"Wykryto wyciek pamięci w Use Case! Przyrost: {res.heap_delta_bytes} B. "
            f"Traces: {res.top_allocations}",
        )
