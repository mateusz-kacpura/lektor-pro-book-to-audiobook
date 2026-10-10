"""
tests.unit.test_book_status_use_case
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Testy jednostkowe przypadku użycia GetBookStatusUseCase oraz FileSystemVoiceDiscoveryAdapter.
100% izolacji od I/O z wykorzystaniem atrap (Fakes).
Ścisłe typowanie bez Any.
"""

import tempfile
import unittest
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

from lektor.adapters.audio.voice_scanner import FileSystemVoiceDiscoveryAdapter
from lektor.application.dtos import GetBookStatusQuery
from lektor.application.ports.audio_ports import (
    AudioStitcherProtocol,
    VoiceDiscoveryProtocol,
)
from lektor.application.ports.storage_ports import (
    BookRepositoryProtocol,
    PageRepositoryProtocol,
)
from lektor.application.ports.telemetry_ports import JobStatusProviderProtocol
from lektor.application.use_cases.get_book_status import GetBookStatusUseCase
from lektor.domain.audio_models import AudioBuffer, make_audio_buffer, SynthesisStats
from lektor.domain.book_models import Book, BookMetadata, BookPaths
from lektor.domain.conversion_models import DocumentScan


class FakeBookRepository(BookRepositoryProtocol):
    def __init__(self, book: Book) -> None:
        self._book = book

    def get_book(self, slug_or_title: str) -> Book | None:
        return self._book if self._book.slug == slug_or_title else None

    def list_books(self) -> Sequence[Book]:
        return [self._book]

    def get_active_book(self) -> Book:
        return self._book

    def get_book_stats(self, slug: str) -> tuple[int, int, int]:
        return 1, 1, 1

    def get_existing_scans(self, slug: str) -> Sequence[DocumentScan]:
        return ()

    def pdf_exists(self, slug: str) -> bool:
        return False

    def set_active_book(self, slug: str) -> Book:
        return self._book

    def save_metadata(self, slug: str, metadata: BookMetadata) -> None:
        pass

    def create_book(
        self,
        title: str,
        slug: str,
        author: str = "",
        language: str = "pl",
        description: str = "",
    ) -> Book:
        return self._book

    def save_pdf(self, slug: str, filename: str, content: bytes) -> Path:
        return Path("/fake/path.pdf")


class FakePageRepository(PageRepositoryProtocol):
    def __init__(self, pages: list[Path], audio_files: set[str], titles: dict[str, str]) -> None:
        self._pages = pages
        self._audio_files = audio_files
        self._titles = titles

    def read_markdown(self, path: Path) -> str:
        return self._titles.get(path.stem, f"# {path.stem.replace('_', ' ').title()}")

    def list_pages(self, directory: Path, pattern: str = "*.md") -> Sequence[Path]:
        return self._pages

    def page_exists(self, path: Path, min_bytes: int = 0) -> bool:
        return True

    def get_page_size(self, path: Path) -> int:
        return 100

    def write_markdown(self, path: Path, content: str) -> None:
        pass

    def save_preview(self, path: Path, text: str) -> None:
        pass

    def save_state(self, path: Path, state_dict: dict[str, object] | SynthesisStats) -> None:
        pass

    def audio_exists(self, path: Path, min_bytes: int = 1000) -> bool:
        return path.stem in self._audio_files


class FakeAudioStitcher(AudioStitcherProtocol):
    def stitch_segments(
        self,
        audio_segments: Sequence[tuple[AudioBuffer | Sequence[float], int]]
    ) -> AudioBuffer:
        return make_audio_buffer(np.zeros(10, dtype=np.float32))

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
        return output_path

    def get_duration_sec(self, audio: AudioBuffer | Sequence[float]) -> float:
        return 12.5

    def audio_exists(self, output_path: Path, min_bytes: int = 0) -> bool:
        return True

    def get_file_size_kb(self, output_path: Path) -> float:
        return 150.0

    def get_file_duration_sec(self, output_path: Path) -> float:
        return 42.0


class FakeJobStatusProvider(JobStatusProviderProtocol):
    def __init__(
        self,
        batch_running: bool = False,
        stopping: bool = False,
        active_gen: Optional[str] = None,
    ) -> None:
        self._batch_running = batch_running
        self._stopping = stopping
        self._active_gen = active_gen

    def is_batch_running(self) -> bool:
        return self._batch_running

    def is_stopping(self) -> bool:
        return self._stopping

    def get_active_generation(self) -> Optional[str]:
        return self._active_gen

    def get_current_params_dict(self) -> dict[str, object]:
        return {"temperature": 0.35, "cfg_weight": 0.7}


class FakeVoiceDiscovery(VoiceDiscoveryProtocol):
    def discover_voices(self) -> list[dict[str, str]]:
        return [{"name": "Lektor PL", "path": "/voices/pl.wav"}]


class TestGetBookStatusUseCase(unittest.TestCase):
    """Testy jednostkowe przypadku użycia GetBookStatusUseCase."""

    def test_get_book_status_success_with_ready_and_pending_pages(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            book_dir = base / "books" / "test_book"
            pages_dir = book_dir / "pages"
            audio_dir = book_dir / "audio"
            pages_dir.mkdir(parents=True, exist_ok=True)
            audio_dir.mkdir(parents=True, exist_ok=True)

            paths = BookPaths(
                root_dir=book_dir,
                pages_dir=pages_dir,
                audio_dir=audio_dir,
                scans_dir=book_dir / "scans",
                images_dir=book_dir / "images",
            )
            meta = BookMetadata(title="Test Clean Book", slug="test_book", total_pages=2)
            book = Book(metadata=meta, paths=paths)

            page1 = pages_dir / "page_0001.md"
            page2 = pages_dir / "page_0002.md"

            book_repo = FakeBookRepository(book)
            page_repo = FakePageRepository(
                pages=[page1, page2],
                audio_files={"page_0001"},
                titles={"page_0001": "# Wstęp do Architektury", "page_0002": "# Zasady SOLID"},
            )
            stitcher = FakeAudioStitcher()
            voice_disc = FakeVoiceDiscovery()
            job_status = FakeJobStatusProvider(active_gen="page_0002")

            use_case = GetBookStatusUseCase(
                book_repository=book_repo,
                page_repository=page_repo,
                audio_stitcher=stitcher,
                voice_discovery=voice_disc,
                job_status_provider=job_status,
            )

            status = use_case.execute(GetBookStatusQuery())

            self.assertEqual(status.book_title, "Test Clean Book")
            self.assertEqual(status.total_pages, 2)
            self.assertEqual(status.ready_count, 1)
            self.assertEqual(status.latest_ready_page, "page_0001")
            self.assertEqual(status.active_generation, "page_0002")
            self.assertEqual(len(status.pages), 2)

            # Strona 1: gotowa
            p1 = status.pages[0]
            self.assertEqual(p1["id"], "page_0001")
            self.assertEqual(p1["status"], "ready")
            self.assertTrue(p1["has_wav"])
            self.assertEqual(p1["title"], "Wstęp do Architektury")

            # Strona 2: w trakcie generowania
            p2 = status.pages[1]
            self.assertEqual(p2["id"], "page_0002")
            self.assertEqual(p2["status"], "generating")
            self.assertFalse(p2["has_wav"])
            self.assertEqual(p2["title"], "Zasady SOLID")

            # Głosy i parametry
            self.assertEqual(len(status.available_voices), 1)
            self.assertEqual(status.available_voices[0]["name"], "Lektor PL")
            self.assertEqual(status.current_params["temperature"], 0.35)

    def test_voice_scanner_adapter_discovers_voices_without_hardcoded_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            default_voice = base / "default.wav"
            default_voice.write_bytes(b"RIFF dummy wav")
            voices_dir = base / "voices"
            voices_dir.mkdir(parents=True, exist_ok=True)
            custom_voice = voices_dir / "custom_actor.wav"
            custom_voice.write_bytes(b"RIFF dummy custom wav")

            adapter = FileSystemVoiceDiscoveryAdapter(data_dir=base, default_voice=default_voice)
            discovered = adapter.discover_voices()

            self.assertGreaterEqual(len(discovered), 2)
            paths = [v["path"] for v in discovered]
            self.assertIn(str(default_voice), paths)
            self.assertIn(str(custom_voice), paths)


if __name__ == "__main__":
    unittest.main()