"""
tests.unit.test_conversion_use_cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Testy jednostkowe przypadków użycia rurociągu konwersji i zarządzania książkami.
100% izolacji od I/O z wykorzystaniem sztucznych atrap (Fakes).
"""

import tempfile
import unittest
from pathlib import Path
from typing import AsyncIterator, Optional, Sequence

from lektor.application.dtos import (
    RenderScansCommand,
    RenderScansStreamCommand,
    StartConversionCommand,
    SwitchActiveBookCommand,
)
from lektor.application.ports.ocr_ports import (
    PdfSplitterProtocol,
    VisionTranslatorProtocol,
)
from lektor.application.ports.storage_ports import (
    BookRepositoryProtocol,
    PageRepositoryProtocol,
)
from lektor.application.ports.telemetry_ports import (
    GpuTelemetryProtocol,
    TelemetryBroadcasterProtocol,
)
from lektor.application.use_cases.convert_pdf_book import ConvertPdfBookUseCase
from lektor.application.use_cases.list_books import ListBooksUseCase
from lektor.application.use_cases.render_pdf_scans import RenderPdfScansUseCase
from lektor.application.use_cases.render_scans_stream import RenderPdfScansStreamUseCase
from lektor.application.use_cases.switch_active_book import SwitchActiveBookUseCase
from lektor.domain.book_models import Book, BookMetadata, BookPaths
from lektor.domain.conversion_models import (
    BookSlug,
    ConversionJob,
    ConversionTaskId,
    ConversionTaskState,
    ConversionTelemetry,
    DocumentScan,
    TranslatedMarkdownPage,
    create_page_number,
)

# --- Atrapy Protokołów (In-Memory Fakes) ---

class FakePdfSplitter(PdfSplitterProtocol):
    def __init__(self, page_count: int = 3) -> None:
        self.page_count = page_count

    def get_page_count(self, pdf_path: Path) -> int:
        return self.page_count

    def split_pdf(
        self,
        pdf_path: Path,
        output_dir: Path,
        dpi: int = 300,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
    ) -> Sequence[DocumentScan]:
        scans: list[DocumentScan] = []
        start = start_page if start_page is not None else 1
        end = min(end_page, self.page_count) if end_page is not None else self.page_count
        for i in range(start, end + 1):
            pn = create_page_number(i)
            fake_path = output_dir / f"page_{i:03d}.jpg"
            # 100% czystej izolacji w pamięci bez fizycznego zapisu na dysku
            scans.append(DocumentScan(page_number=pn, scan_path=fake_path, dpi=dpi))
        return tuple(scans)

    def render_page(
        self,
        pdf_path: Path,
        page_index_0based: int,
        output_path: Path,
        dpi: int = 300,
    ) -> None:
        pass


class FakeVisionTranslator(VisionTranslatorProtocol):
    def __init__(self, fail_on_page: int = -1) -> None:
        self.fail_on_page = fail_on_page
        self.translated_pages: list[int] = []

    def translate_scan(
        self,
        scan: DocumentScan,
        custom_prompt: Optional[str] = None,
        target_language: str = "pl",
        source_language: Optional[str] = None,
    ) -> TranslatedMarkdownPage:
        pn_val = int(scan.page_number)
        if pn_val == self.fail_on_page:
            raise RuntimeError(f"Błąd symulowany dla strony {pn_val}")

        self.translated_pages.append(pn_val)
        content = f"""# Strona {pn_val}: Tłumaczenie Cloud Native ({target_language})
        Oto przetłumaczony tekst oraz diagram:
        ```mermaid
        flowchart TD
            A[Węzeł {pn_val}] --> B[Serwer]
        """
        return TranslatedMarkdownPage(page_number=scan.page_number, markdown_content=content)

class FakeBroadcaster(TelemetryBroadcasterProtocol):
    def __init__(self) -> None:
        self.emitted: list[ConversionTelemetry] = []

    def broadcast(self, telemetry: ConversionTelemetry) -> None:
        self.emitted.append(telemetry)

    async def subscribe(self, task_id: ConversionTaskId) -> AsyncIterator[ConversionTelemetry]:
        for t in self.emitted:
            yield t


class FakeGpuTelemetry(GpuTelemetryProtocol):
    def get_gpu_stats(self) -> tuple[float, float, float]:
        return 1200.0, 12000.0, 15.0


class FakeBookRepository(BookRepositoryProtocol):
    """Atrapa repozytorium książek w 100% w pamięci RAM, bez I/O dyskowego."""

    def __init__(self) -> None:
        self.books: dict[str, Book] = {}
        self.active_slug: str = ""
        self.stats: dict[str, tuple[int, int, int]] = {}

    def get_book(self, slug_or_title: str) -> Book | None:
        return self.books.get(slug_or_title)

    def list_books(self) -> Sequence[Book]:
        return list(self.books.values())

    def get_active_book(self) -> Book:
        if self.active_slug and self.active_slug in self.books:
            return self.books[self.active_slug]
        if self.books:
            return next(iter(self.books.values()))
        return self.create_book("Domyślna", "default")

    def set_active_book(self, slug: str) -> Book:
        self.active_slug = slug
        if slug in self.books:
            return self.books[slug]
        return self.create_book(title=slug.replace("_", " ").title(), slug=slug)

    def get_book_stats(self, slug: str) -> tuple[int, int, int]:
        if slug in self.stats:
            return self.stats[slug]
        return 1, 0, 0

    def save_metadata(self, slug: str, metadata: BookMetadata) -> None:
        pass

    def create_book(
        self,
        title: str,
        slug: str,
        author: str = "",
        language: str = "pl",
        description: str = "",
        original_pdf: Optional[Path] = None,
    ) -> Book:
        b_paths = BookPaths(
            root_dir=Path("virtual") / slug,
            pages_dir=Path("virtual") / slug / "pages",
            scans_dir=Path("virtual") / slug / "scans",
            images_dir=Path("virtual") / slug / "images",
            audio_dir=Path("virtual") / slug / "audio",
            original_pdf=original_pdf,
        )
        book = Book(
            metadata=BookMetadata(title=title, slug=slug, author=author, language=language, description=description),
            paths=b_paths,
        )
        self.books[slug] = book
        return book

    def save_pdf(self, slug: str, filename: str, content: bytes) -> Path:
        return Path("virtual") / slug / filename

    def get_existing_scans(self, slug: str) -> Sequence[DocumentScan]:
        return ()

    def pdf_exists(self, slug: str) -> bool:
        return True


class FakePageRepository(PageRepositoryProtocol):
    def __init__(self) -> None:
        self.saved_pages: dict[str, str] = {}

    def read_markdown(self, path: Path) -> str:
        return self.saved_pages.get(str(path), "")

    def write_markdown(self, path: Path, content: str) -> None:
        self.saved_pages[str(path)] = content

    def list_pages(self, directory: Path, pattern: str = "*.md") -> Sequence[Path]:
        return [Path(p) for p in self.saved_pages.keys()]

    def page_exists(self, path: Path, min_bytes: int = 0) -> bool:
        return str(path) in self.saved_pages and len(self.saved_pages[str(path)]) >= min_bytes

    def get_page_size(self, path: Path) -> int:
        return len(self.saved_pages.get(str(path), ""))

    def save_preview(self, path: Path, text: str) -> None:
        pass

    def audio_exists(self, path: Path, min_bytes: int = 1000) -> bool:
        return False

    def save_state(self, path: Path, state_dict: object) -> None:
        pass


class TestConversionUseCases(unittest.TestCase):
    """Testy jednostkowe logiki Use Cases dla konwersji i zarządzania książkami."""

    def test_switch_and_list_books_use_cases(self) -> None:
        book_repo = FakeBookRepository()

        # Rejestracja testowej książki (w 100% w pamięci RAM)
        book_repo.create_book(title="Cloud Go", slug="cloud_go")
        book_repo.stats["cloud_go"] = (1, 0, 0)

        # Brak ignorowania typów, pełna zgodność z protokołem
        switch_uc = SwitchActiveBookUseCase(book_repo)
        meta = switch_uc.execute(SwitchActiveBookCommand(slug=BookSlug("cloud_go")))
        self.assertEqual(meta.slug, "cloud_go")
        self.assertTrue(meta.is_active)
        self.assertEqual(meta.total_pages, 1)

        list_uc = ListBooksUseCase(book_repo)
        all_books = list_uc.execute()
        self.assertEqual(len(all_books), 1)
        self.assertEqual(all_books[0].slug, "cloud_go")
        self.assertTrue(all_books[0].is_active)

    def test_convert_pdf_book_full_flow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            temp_path = Path(td)
            pdf_file = temp_path / "sample.pdf"
            pdf_file.write_bytes(b"%PDF-1.4 Fake PDF Content")

            splitter = FakePdfSplitter(page_count=3)
            translator = FakeVisionTranslator()
            page_repo = FakePageRepository()
            broadcaster = FakeBroadcaster()
            gpu = FakeGpuTelemetry()
            book_repo = FakeBookRepository()
            book_repo.create_book(title="Sample Book", slug="sample_book")

            use_case = ConvertPdfBookUseCase(
                pdf_splitter=splitter,
                vision_translator=translator,
                page_repository=page_repo,
                broadcaster=broadcaster,
                gpu_telemetry=gpu,
                book_repository=book_repo,
            )

            job = ConversionJob.create(BookSlug("sample_book"), pdf_file)
            cmd = StartConversionCommand(
                pdf_path=pdf_file,
                book_slug=BookSlug("sample_book"),
                scans_dir=temp_path / "scans",
                pages_dir=temp_path / "pages",
            )

            use_case.execute(cmd, job)

            self.assertEqual(job.state, ConversionTaskState.COMPLETED)
            self.assertEqual(job.completed_pages, 3)
            self.assertEqual(len(job.failed_pages), 0)
            self.assertEqual(len(page_repo.saved_pages), 3)
            self.assertGreater(len(broadcaster.emitted), 3)

    def test_convert_pdf_book_page_failure_resilience(self) -> None:
        """Weryfikuje Regułę 13: błąd pojedynczej strony nie przerywa całego zadania."""
        with tempfile.TemporaryDirectory() as td:
            temp_path = Path(td)
            pdf_file = temp_path / "sample.pdf"
            pdf_file.write_bytes(b"%PDF-1.4 Fake PDF Content")

            splitter = FakePdfSplitter(page_count=3)
            # Strona 2 rzuca błąd
            translator = FakeVisionTranslator(fail_on_page=2)
            page_repo = FakePageRepository()
            broadcaster = FakeBroadcaster()
            gpu = FakeGpuTelemetry()
            book_repo = FakeBookRepository()
            book_repo.create_book(title="Resilience Book", slug="resilience_book")

            use_case = ConvertPdfBookUseCase(
                pdf_splitter=splitter,
                vision_translator=translator,
                page_repository=page_repo,
                broadcaster=broadcaster,
                gpu_telemetry=gpu,
                book_repository=book_repo,
            )

            job = ConversionJob.create(BookSlug("resilience_book"), pdf_file)
            cmd = StartConversionCommand(
                pdf_path=pdf_file,
                book_slug=BookSlug("resilience_book"),
                scans_dir=temp_path / "scans",
                pages_dir=temp_path / "pages",
            )

            use_case.execute(cmd, job)

            self.assertEqual(job.state, ConversionTaskState.COMPLETED)
            self.assertEqual(job.completed_pages, 2)
            self.assertIn(2, job.failed_pages)
            # Zapisano pomyślne strony 1 i 3
            self.assertEqual(len(page_repo.saved_pages), 2)

    def test_render_pdf_scans_stream_use_case(self) -> None:
        """Weryfikuje strumieniowe renderowanie stron PDF w RenderPdfScansStreamUseCase."""
        import asyncio

        with tempfile.TemporaryDirectory() as td:
            temp_path = Path(td)
            pdf_file = temp_path / "sample.pdf"
            pdf_file.write_bytes(b"%PDF-1.4 Fake PDF Content")

            splitter = FakePdfSplitter(page_count=2)
            book_repo = FakeBookRepository()
            book_repo.create_book(title="Stream Book", slug="stream_book", original_pdf=pdf_file)

            use_case = RenderPdfScansStreamUseCase(
                book_repository=book_repo,
                pdf_splitter=splitter,
            )

            cmd = RenderScansStreamCommand(
                book_slug="stream_book",
                dpi=150,
                start_page=1,
                end_page=2,
            )

            async def _collect_events() -> list[dict[str, object]]:
                events: list[dict[str, object]] = []
                async for event in use_case.execute_stream(cmd):
                    events.append(event)
                return events

            events = asyncio.run(_collect_events())

            self.assertEqual(len(events), 4)
            self.assertEqual(events[0]["status"], "started")
            self.assertEqual(events[1]["status"], "rendering")
            self.assertEqual(events[1]["current_page"], 1)
            self.assertEqual(events[2]["status"], "rendering")
            self.assertEqual(events[2]["current_page"], 2)
            self.assertEqual(events[3]["status"], "completed")
            self.assertEqual(events[3]["rendered_count"], 2)

    def test_render_pdf_scans_use_case(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            temp_path = Path(td)
            pdf_file = temp_path / "sample.pdf"
            pdf_file.write_bytes(b"%PDF-1.4 Fake PDF Content")

            splitter = FakePdfSplitter(page_count=3)
            book_repo = FakeBookRepository()
            book_repo.create_book(title="Scans Book", slug="scans_book", original_pdf=pdf_file)

            use_case = RenderPdfScansUseCase(
                book_repository=book_repo,
                pdf_splitter=splitter,
            )

            cmd = RenderScansCommand(
                book_slug="scans_book",
                dpi=300,
                start_page=1,
                end_page=3,
            )

            res = use_case.execute(cmd)
            self.assertEqual(res.book_slug, "scans_book")
            self.assertEqual(res.scans_created, 3)
            self.assertIn("3 skanów", res.message)
