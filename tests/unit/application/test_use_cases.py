"""
Testy jednostkowe przypadków użycia (Use Cases).
100% izolacji od I/O, bazy danych, dysku i modeli ML dzięki odwróceniu zależności (DIP).
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

from lektor.application.dtos import (
    BatchSynthesisCommand,
    ConvertBookCommand,
    PreviewPageQuery,
    SynthesizePageCommand,
    SynthesizeSnippetCommand,
)
from lektor.application.ports.audio_ports import (
    AudioCacheProtocol,
    AudioStitcherProtocol,
    TTSEngineProtocol,
)
from lektor.application.ports.ocr_ports import (
    BookMarkdownFormatterProtocol,
    VisionTranslatorProtocol,
)
from lektor.application.ports.resource_ports import AIModelArbiterProtocol
from lektor.application.ports.storage_ports import PageRepositoryProtocol
from lektor.application.ports.telemetry_ports import ProgressReporterProtocol
from lektor.application.use_cases.batch_synthesis import BatchSynthesisUseCase
from lektor.application.use_cases.convert_book import ConvertBookUseCase
from lektor.application.use_cases.preview_page import PreviewPageUseCase
from lektor.application.use_cases.synthesize_page import SynthesizePageUseCase
from lektor.application.use_cases.synthesize_snippet import SynthesizeMarkdownSnippetUseCase
from lektor.domain.audio_models import (
    AudioBuffer,
    PageNumber,
    SynthesisConfig,
    SynthesisResult,
    SynthesisStats,
    make_audio_buffer,
)
from lektor.domain.conversion_models import DocumentScan, TranslatedMarkdownPage
from lektor.domain.normalization import TextNormalizationService
from lektor.domain.resource_models import ModelSlotId, VramSnapshot

# --- Atrapy Protokołów (In-Memory Fakes) ---


class FakeTTSEngine(TTSEngineProtocol):
    def __init__(self) -> None:
        self.load_calls = 0
        self.synthesize_calls: list[tuple[str, str]] = []

    def load_model(self) -> None:
        self.load_calls += 1

    def is_loaded(self) -> bool:
        return self.load_calls > 0

    def synthesize_segment(self, text: str, lang: str = "pl") -> AudioBuffer:
        self.synthesize_calls.append((text, lang))
        return make_audio_buffer(np.array([0.1, 0.2, 0.3], dtype=np.float32))

    def unload_model(self) -> None:
        self.load_calls = 0


class FakeAudioStitcher(AudioStitcherProtocol):
    def __init__(self) -> None:
        self.save_calls: list[Path] = []

    def stitch_segments(
        self,
        audio_segments: Sequence[tuple[AudioBuffer | Sequence[float], int]]
    ) -> AudioBuffer:
        out: list[float] = []
        for chunk, _ in audio_segments:
            out.extend(list(chunk))
        return make_audio_buffer(np.array(out, dtype=np.float32))

    def normalize_volume(
        self,
        audio: AudioBuffer,
        target_peak: float = 0.95
    ) -> AudioBuffer:
        return audio

    def create_silence(self, duration_ms: int) -> AudioBuffer:
        return make_audio_buffer(np.zeros(10, dtype=np.float32))

    def save_audio(
        self,
        audio: AudioBuffer,
        output_path: Path,
        format: str = "wav"
    ) -> Path:
        self.save_calls.append(output_path)
        return output_path

    def get_duration_sec(self, audio: AudioBuffer | Sequence[float]) -> float:
        return float(len(audio)) / 10.0

    def audio_exists(self, path: Path, min_bytes: int = 1000) -> bool:
        return path in self.save_calls

    def get_file_size_kb(self, path: Path) -> float:
        return 10.0 if path in self.save_calls else 0.0

    def get_file_duration_sec(self, output_path: Path) -> float:
        return 1.0 if output_path in self.save_calls else 0.0


class FakePageRepository(PageRepositoryProtocol):
    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.existing_audio: set[str] = set()
        self.saved_previews: dict[str, str] = {}
        self.saved_states: dict[str, dict[str, object] | SynthesisStats] = {}

    def read_markdown(self, path: Path) -> str:
        key = str(path)
        if key not in self.files:
            raise FileNotFoundError(f"Brak pliku {key}")
        return self.files[key]

    def write_markdown(self, path: Path, content: str) -> None:
        self.files[str(path)] = content

    def page_exists(self, path: Path, min_bytes: int = 1) -> bool:
        return str(path) in self.files and len(self.files.get(str(path), "")) >= min_bytes

    def get_page_size(self, path: Path) -> int:
        return len(self.files.get(str(path), ""))

    def list_pages(self, directory: Path, pattern: str = "*.md") -> Sequence[Path]:
        return [Path(k) for k in sorted(self.files.keys()) if k.endswith(".md")]

    def save_preview(self, path: Path, text: str) -> None:
        self.saved_previews[str(path)] = text

    def audio_exists(self, path: Path, min_bytes: int = 1000) -> bool:
        return str(path) in self.existing_audio

    def save_state(self, path: Path, state_dict: dict[str, object] | SynthesisStats) -> None:
        self.saved_states[str(path)] = state_dict


class FakeVisionTranslator(VisionTranslatorProtocol):
    def __init__(self) -> None:
        self.translated_scans: list[DocumentScan] = []

    def translate_scan(
        self,
        scan: DocumentScan,
        custom_prompt: Optional[str] = None,
        target_language: str = "pl",
        source_language: Optional[str] = None,
    ) -> TranslatedMarkdownPage:
        self.translated_scans.append(scan)
        return TranslatedMarkdownPage(
            page_number=scan.page_number,
            markdown_content=f"Treść strony {scan.scan_path.stem} ({target_language})",
            diagrams=(),
            code_blocks_count=0,
        )


class FakeMarkdownFormatter(BookMarkdownFormatterProtocol):
    def format_markdown(
        self,
        raw_md: str,
        page_num: PageNumber,
        img_name: str,
        book_dir_name: str = "scans",
    ) -> str:
        return f"# Strona {int(page_num):03d}\n\n{raw_md}"


class FakeProgressReporter(ProgressReporterProtocol):
    def __init__(self) -> None:
        self.started_pages: list[Path] = []
        self.completed_results: list[SynthesisResult] = []
        self.skipped_pages: list[tuple[Path, str]] = []

    def on_page_start(self, page_path: Path, current_idx: int, total_pages: int) -> None:
        self.started_pages.append(page_path)

    def on_page_complete(self, result: SynthesisResult) -> None:
        self.completed_results.append(result)

    def on_skipped(self, page_path: Path, reason: str) -> None:
        self.skipped_pages.append((page_path, reason))

    def on_error(self, page_path: Path, error: Exception) -> None:
        pass

    def check_cancellation(self) -> bool:
        return False




class FakeModelArbiter(AIModelArbiterProtocol):
    def __init__(self) -> None:
        self.acquired: list[ModelSlotId] = []
        self.released: list[ModelSlotId] = []

    def acquire(self, slot_id: ModelSlotId) -> None:
        self.acquired.append(slot_id)

    def release(self, slot_id: ModelSlotId) -> None:
        self.released.append(slot_id)

    def release_all(self) -> None:
        self.released.extend(self.acquired)

    def get_active_slot(self) -> Optional[ModelSlotId]:
        return self.acquired[-1] if self.acquired else None

    def get_vram_snapshot(self) -> VramSnapshot:
        return VramSnapshot(used_mb=0.0, total_mb=0.0, free_mb=0.0)

# --- Testy Jednostkowe Przypadków Użycia ---


class TestUseCases(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.tts = FakeTTSEngine()
        self.stitcher = FakeAudioStitcher()
        self.repo = FakePageRepository()
        self.normalizer = TextNormalizationService()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_synthesize_page_normal_flow(self) -> None:
        uc = SynthesizePageUseCase(
            tts_engine=self.tts,
            audio_stitcher=self.stitcher,
            page_repository=self.repo,
            normalization_service=self.normalizer,
        )

        md_path = Path("pages/page_001.md")
        out_dir = Path("audio_output")
        self.repo.write_markdown(md_path, "To jest testowa strona z tekstem.")

        cmd = SynthesizePageCommand(markdown_path=md_path, output_dir=out_dir)
        res = uc.execute(cmd)

        self.assertFalse(res.skipped_existing)
        self.assertGreater(len(res.segments), 0)
        self.assertGreater(self.tts.load_calls, 0)
        self.assertEqual(len(self.stitcher.save_calls), 1)
        self.assertIn(str(out_dir / "page_001_normalized.txt"), self.repo.saved_previews)

    def test_synthesize_page_skip_existing(self) -> None:
        uc = SynthesizePageUseCase(
            tts_engine=self.tts,
            audio_stitcher=self.stitcher,
            page_repository=self.repo,
            normalization_service=self.normalizer,
        )

        md_path = Path("pages/page_002.md")
        out_dir = Path("audio_output")
        expected_audio = out_dir / "page_002.wav"
        self.repo.existing_audio.add(str(expected_audio))

        cmd = SynthesizePageCommand(markdown_path=md_path, output_dir=out_dir, skip_existing=True)
        res = uc.execute(cmd)

        self.assertTrue(res.skipped_existing)
        self.assertEqual(self.tts.load_calls, 0)
        self.assertEqual(len(self.stitcher.save_calls), 0)

    def test_preview_page_use_case(self) -> None:
        uc = PreviewPageUseCase(
            page_repository=self.repo,
            normalization_service=self.normalizer,
        )
        query = PreviewPageQuery(raw_text="Rozdział 1 — Architektura\n\nPierwszy akapit książki.")
        res = uc.execute(query)

        self.assertGreater(res.segment_count, 0)
        self.assertGreater(res.total_chars, 0)
        self.assertGreater(res.total_words, 0)
        self.assertIn("Pierwszy akapit", res.formatted_preview)

    def test_batch_synthesis_use_case(self) -> None:
        synthesize_uc = SynthesizePageUseCase(
            tts_engine=self.tts,
            audio_stitcher=self.stitcher,
            page_repository=self.repo,
            normalization_service=self.normalizer,
        )
        reporter = FakeProgressReporter()
        batch_uc = BatchSynthesisUseCase(
            synthesize_page_uc=synthesize_uc,
            page_repository=self.repo,
            progress_reporter=reporter,
        )

        self.repo.write_markdown(Path("pages/page_001.md"), "Strona pierwsza")
        self.repo.write_markdown(Path("pages/page_002.md"), "Strona druga")

        bcmd = BatchSynthesisCommand(pages_dir=Path("pages"), output_dir=Path("audio_output"), skip_existing=False)
        results = batch_uc.execute(bcmd)

        self.assertEqual(len(results), 2)
        self.assertEqual(len(reporter.started_pages), 2)
        self.assertEqual(len(reporter.completed_results), 2)

    def test_synthesize_markdown_snippet_releases_gpu_lease(self) -> None:
        arbiter = FakeModelArbiter()
        uc = SynthesizeMarkdownSnippetUseCase(
            tts_engine=self.tts,
            audio_stitcher=self.stitcher,
            normalization_service=self.normalizer,
            model_arbiter=arbiter,
        )
        cmd = SynthesizeSnippetCommand(
            snippet_id="snippet_gpu",
            markdown="Tekst do zwolnienia modelu GPU.",
            output_path=self.temp_dir / "gpu.wav",
            force=True,
        )

        uc.execute(cmd)

        from lektor.domain.resource_models import SLOT_AUDIO_TTS
        self.assertEqual(arbiter.acquired, [SLOT_AUDIO_TTS])
        self.assertEqual(arbiter.released, [SLOT_AUDIO_TTS])

    def test_convert_book_use_case(self) -> None:
        translator = FakeVisionTranslator()
        formatter = FakeMarkdownFormatter()
        reporter = FakeProgressReporter()
        uc = ConvertBookUseCase(
            vision_translator=translator,
            markdown_formatter=formatter,
            page_repository=self.repo,
            progress_reporter=reporter,
        )

        # Stwórz wirtualne pliki stron
        in_dir = Path("mock_images")
        out_dir = Path("mock_pages")

        # Symuluj pliki obrazów w repozytorium przez podmienienie _get_sorted_images
        uc._get_sorted_images = lambda _: [(1, Path("mock_images/page-001.jpg")), (2, Path("mock_images/page-002.jpg"))]  # type: ignore

        cmd = ConvertBookCommand(input_dir=in_dir, output_dir=out_dir, start_page=1, end_page=2)
        res = uc.execute(cmd)

        self.assertEqual(res.processed_count, 2)
        self.assertEqual(len(translator.translated_scans), 2)
        self.assertIn(str(out_dir / "page_001.md"), self.repo.files)
        self.assertIn(str(out_dir / "page_002.md"), self.repo.files)

    def test_synthesize_markdown_snippet_use_case(self) -> None:
        cache = FakeAudioCache()
        uc = SynthesizeMarkdownSnippetUseCase(
            tts_engine=self.tts,
            audio_stitcher=self.stitcher,
            normalization_service=self.normalizer,
            audio_cache=cache,
        )

        out_wav = self.temp_dir / "output.wav"
        cmd = SynthesizeSnippetCommand(
            snippet_id="snippet_1",
            markdown="# Nagłówek\nTo jest testowy snippet do syntezy.",
            output_path=out_wav,
        )

        res = uc.execute(cmd)

        self.assertEqual(res.snippet_id, "snippet_1")
        self.assertEqual(res.audio_path, out_wav)
        self.assertGreater(res.segment_count, 0)
        self.assertFalse(res.skipped_existing)
        self.assertGreater(len(cache.storage), 0)

        # Druga synteza z cache
        res2 = uc.execute(cmd)
        self.assertEqual(res2.snippet_id, "snippet_1")


class FakeAudioCache(AudioCacheProtocol):
    def __init__(self) -> None:
        self.storage: dict[str, AudioBuffer] = {}

    def get(
        self,
        text: str,
        lang: str = "pl",
        voice: Optional[str] = None,
        config: Optional[SynthesisConfig] = None,
        temperature: float = 0.35,
        cfg_weight: float = 0.7,
    ) -> Optional[AudioBuffer]:
        return self.storage.get(text)

    def put(
        self,
        text: str,
        audio: AudioBuffer,
        lang: str = "pl",
        voice: Optional[str] = None,
        config: Optional[SynthesisConfig] = None,
        temperature: float = 0.35,
        cfg_weight: float = 0.7,
        sample_rate: int = 24000,
    ) -> None:
        self.storage[text] = audio


if __name__ == "__main__":
    unittest.main()

