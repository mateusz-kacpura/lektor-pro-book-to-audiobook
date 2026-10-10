"""
lektor.application.use_cases.convert_pdf_book
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Main use case: Converting PDF file into JPG scans, multimodal AI analysis
(multilingual translation 140+ languages, code protection, Mermaid diagrams), and live telemetry broadcasting.
"""

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from ...domain.book_models import BookMetadata
from ...domain.conversion_models import (
    ConversionJob,
    ConversionTaskState,
    ConversionTelemetry,
    DocumentScan,
    create_page_number,
    format_page_filename,
)
from ...domain.normalizers.glossary import TechnicalGlossaryService
from ...domain.validators.markdown_validator import MarkdownPageValidationService
from ..dtos import StartConversionCommand
from ..ports.ocr_ports import PdfSplitterProtocol, VisionTranslatorProtocol
from ..ports.resource_ports import AIModelArbiterProtocol
from ..ports.storage_ports import BookRepositoryProtocol, PageRepositoryProtocol
from ..ports.telemetry_ports import GpuTelemetryProtocol, TelemetryBroadcasterProtocol


@dataclass(frozen=True)
class _ScanPreparation:
    scans: Sequence[DocumentScan]
    pages_dir: Path
    started_at: float


@dataclass(frozen=True)
class _PendingScanContext:
    command: StartConversionCommand
    job: ConversionJob
    scans: Sequence[DocumentScan]
    total_pages: int
    pages_dir: Path
    started_at: float
    completed_pages: int


@dataclass(frozen=True)
class _PageContext:
    command: StartConversionCommand
    job: ConversionJob
    scan: DocumentScan
    output_path: Path
    progress_index: int
    total_pages: int
    remaining_pages: int
    started_at: float
    completed_ai_pages: int
    completed_ai_duration_sec: float


class ConvertPdfBookUseCase:
    """Orchestrates the PDF splitting pipeline, scan translation, and telemetry broadcasting."""

    def __init__(
        self,
        pdf_splitter: PdfSplitterProtocol,
        vision_translator: VisionTranslatorProtocol,
        page_repository: PageRepositoryProtocol,
        broadcaster: TelemetryBroadcasterProtocol,
        gpu_telemetry: GpuTelemetryProtocol,
        validator: Optional[MarkdownPageValidationService] = None,
        glossary: Optional[TechnicalGlossaryService] = None,
        book_repository: Optional[BookRepositoryProtocol] = None,
        model_arbiter: Optional[AIModelArbiterProtocol] = None,
    ) -> None:
        self._splitter = pdf_splitter
        self._translator = vision_translator
        self._page_repo = page_repository
        self._broadcaster = broadcaster
        self._gpu = gpu_telemetry
        self._validator = validator or MarkdownPageValidationService()
        self._glossary = glossary or TechnicalGlossaryService()
        self._book_repo = book_repository
        self._arbiter = model_arbiter

    def execute(self, cmd: StartConversionCommand, job: ConversionJob) -> None:
        """Executes conversion and always releases the vision model upon completion."""
        if self._arbiter is None:
            self._execute(cmd, job)
            return

        from ...domain.resource_models import SLOT_VISION

        self._arbiter.acquire(SLOT_VISION)
        try:
            self._execute(cmd, job)
        finally:
            self._arbiter.release(SLOT_VISION)

    def _execute(self, cmd: StartConversionCommand, job: ConversionJob) -> None:
        preparation = self._prepare_scans(cmd, job)
        if preparation is None or not preparation.scans:
            if preparation is not None:
                job.transition_to(ConversionTaskState.FAILED)
                self._emit_telemetry(
                    job,
                    current_page=0,
                    step_desc="B\u0142\u0105d: Nie znaleziono \u017cadnych stron do przetworzenia",
                )
            return

        job.transition_to(ConversionTaskState.TRANSLATING)
        active_scans = [
            scan
            for scan in preparation.scans
            if (cmd.start_page is None or int(scan.page_number) >= cmd.start_page)
            and (cmd.end_page is None or int(scan.page_number) <= cmd.end_page)
        ]
        total_active = len(active_scans)
        job.total_pages = total_active
        pending_scans = self._select_pending_scans(active_scans, cmd, preparation.pages_dir)
        context = _PendingScanContext(
            command=cmd,
            job=job,
            scans=pending_scans,
            total_pages=total_active,
            pages_dir=preparation.pages_dir,
            started_at=preparation.started_at,
            completed_pages=total_active - len(pending_scans),
        )
        self._process_pending_scans(context)

        if not job.cancellation_requested:
            job.transition_to(ConversionTaskState.COMPLETED)
            self._emit_telemetry(
                job,
                current_page=total_active,
                step_desc=(
                    f"\U0001f389 Konwersja zako\u0144czona pomy\u015blnie "
                    f"({total_active} stron w j\u0119zyku '{cmd.target_language}')!"
                ),
                elapsed_sec=time.perf_counter() - preparation.started_at,
                progress_pct=100.0,
                remaining_pages=0,
            )

    def _prepare_scans(
        self,
        cmd: StartConversionCommand,
        job: ConversionJob,
    ) -> Optional[_ScanPreparation]:
        if not cmd.pdf_path.exists() or cmd.pdf_path.stat().st_size == 0:
            job.transition_to(ConversionTaskState.FAILED)
            self._emit_telemetry(
                job,
                current_page=0,
                step_desc="B\u0142\u0105d: Plik PDF nie istnieje lub jest pusty",
            )
            return None

        scans_dir, pages_dir = self._resolve_book_directories(cmd)
        started_at = time.perf_counter()
        existing_scans = self._load_existing_scans(cmd.book_slug, scans_dir)
        doc_page_count = self._splitter.get_page_count(cmd.pdf_path)
        requested_pages, missing_pages = self._get_page_range(
            cmd,
            doc_page_count,
            existing_scans,
        )
        scans: Sequence[DocumentScan]

        if not missing_pages and existing_scans:
            scans = tuple(
                DocumentScan(
                    page_number=create_page_number(page_number),
                    scan_path=existing_scans[page_number],
                    dpi=cmd.dpi,
                )
                for page_number in requested_pages
            )
            job.total_pages = len(scans)
            self._emit_telemetry(
                job,
                current_page=0,
                step_desc=(
                    f"Wykryto {len(scans)} gotowych skan\u00f3w JPG. "
                    f"Przechodz\u0119 do analizy AI na j\u0119zyk: {cmd.target_language}..."
                ),
                elapsed_sec=time.perf_counter() - started_at,
            )
            return _ScanPreparation(scans, pages_dir, started_at)

        job.transition_to(ConversionTaskState.SPLITTING_PDF)
        self._emit_telemetry(
            job,
            current_page=0,
            step_desc=(f"Przygotowanie skan\u00f3w PDF do JPG 300 DPI (brakuj\u0105ce: {len(missing_pages)} stron)..."),
        )
        try:
            scans = self._splitter.split_pdf(
                cmd.pdf_path,
                scans_dir,
                dpi=cmd.dpi,
                start_page=cmd.start_page,
                end_page=cmd.end_page,
            )
        except Exception as error:
            job.transition_to(ConversionTaskState.FAILED)
            self._emit_telemetry(
                job,
                current_page=0,
                step_desc="B\u0142\u0105d podzia\u0142u PDF",
                error_msg=str(error),
            )
            return None

        job.total_pages = len(scans)
        return _ScanPreparation(scans, pages_dir, started_at)

    def _resolve_book_directories(self, cmd: StartConversionCommand) -> tuple[Path, Path]:
        if cmd.scans_dir is not None and cmd.pages_dir is not None:
            return cmd.scans_dir, cmd.pages_dir

        if self._book_repo is None:
            base_book_dir = Path("books") / str(cmd.book_slug)
            return base_book_dir / "scans", base_book_dir / "pages"

        book = self._book_repo.get_book(str(cmd.book_slug))
        if book is None:
            book = self._book_repo.create_book(
                title=str(cmd.book_slug).replace("_", " ").title(),
                slug=str(cmd.book_slug),
                language=cmd.target_language,
            )
        elif book.metadata.language != cmd.target_language:
            updated_meta = BookMetadata(
                title=book.metadata.title,
                slug=book.metadata.slug,
                author=book.metadata.author,
                language=cmd.target_language,
                total_pages=book.metadata.total_pages,
                description=book.metadata.description,
                created_at=book.metadata.created_at,
            )
            self._book_repo.save_metadata(str(cmd.book_slug), updated_meta)

        return book.paths.scans_dir, book.paths.pages_dir

    def _load_existing_scans(self, slug: object, scans_dir: Path) -> dict[int, Path]:
        existing_scans: dict[int, Path] = {}
        if self._book_repo is not None:
            for scan in self._book_repo.get_existing_scans(str(slug)):
                existing_scans[int(scan.page_number)] = scan.scan_path
            return existing_scans

        if not scans_dir.exists():
            return existing_scans

        for path in scans_dir.glob("page_*.jpg"):
            match = re.search(r"page_(\d+)", path.name)
            if match and path.stat().st_size > 0:
                existing_scans[int(match.group(1))] = path
        return existing_scans

    @staticmethod
    def _get_page_range(
        cmd: StartConversionCommand,
        doc_page_count: int,
        existing_scans: dict[int, Path],
    ) -> tuple[list[int], list[int]]:
        start_page = cmd.start_page if cmd.start_page is not None and cmd.start_page >= 1 else 1
        end_page = (
            cmd.end_page
            if cmd.end_page is not None and cmd.end_page >= 1
            else (doc_page_count or len(existing_scans) or 1)
        )
        requested_pages = list(range(start_page, end_page + 1))
        missing_pages = [page_number for page_number in requested_pages if page_number not in existing_scans]
        return requested_pages, missing_pages

    def _select_pending_scans(
        self,
        scans: Sequence[DocumentScan],
        cmd: StartConversionCommand,
        pages_dir: Path,
    ) -> list[DocumentScan]:
        pending_scans: list[DocumentScan] = []
        for scan in scans:
            output_path = pages_dir / format_page_filename(scan.page_number, prefix="page_", ext=".md")
            if not cmd.skip_existing or not self._page_repo.page_exists(output_path, min_bytes=50):
                pending_scans.append(scan)
        return pending_scans

    def _process_pending_scans(self, context: _PendingScanContext) -> None:
        completed_ai_pages = 0
        completed_ai_duration_sec = 0.0
        for index, scan in enumerate(context.scans, start=1):
            progress_index = context.completed_pages + index
            remaining_pages = context.total_pages - progress_index
            if self._handle_pause_or_cancel(context.job, scan):
                return

            output_path = context.pages_dir / format_page_filename(
                scan.page_number,
                prefix="page_",
                ext=".md",
            )
            page_context = _PageContext(
                command=context.command,
                job=context.job,
                scan=scan,
                output_path=output_path,
                progress_index=progress_index,
                total_pages=context.total_pages,
                remaining_pages=remaining_pages,
                started_at=context.started_at,
                completed_ai_pages=completed_ai_pages,
                completed_ai_duration_sec=completed_ai_duration_sec,
            )
            completed_ai_pages, completed_ai_duration_sec = self._process_page(page_context)

    def _handle_pause_or_cancel(self, job: ConversionJob, scan: DocumentScan) -> bool:
        if job.cancellation_requested:
            job.transition_to(ConversionTaskState.CANCELLED)
            self._emit_telemetry(
                job,
                current_page=int(scan.page_number),
                step_desc="Zadanie anulowane przez u\u017cytkownika",
            )
            return True

        while job.pause_requested and not job.cancellation_requested:
            job.transition_to(ConversionTaskState.PAUSED)
            self._emit_telemetry(
                job,
                current_page=int(scan.page_number),
                step_desc="Zadanie wstrzymane",
            )
            time.sleep(0.1)

        if job.cancellation_requested:
            job.transition_to(ConversionTaskState.CANCELLED)
            self._emit_telemetry(
                job,
                current_page=int(scan.page_number),
                step_desc="Zadanie anulowane przez u\u017cytkownika",
            )
            return True

        if job.state == ConversionTaskState.PAUSED:
            job.transition_to(ConversionTaskState.TRANSLATING)
        return False

    def _process_page(self, context: _PageContext) -> tuple[int, float]:
        page_start_time = time.perf_counter()
        self._emit_telemetry(
            context.job,
            current_page=int(context.scan.page_number),
            step_desc=(
                f"Strona {int(context.scan.page_number)}/{context.total_pages}: "
                f"Ekstrakcja wizyjna AI na j\u0119zyk '{context.command.target_language}'..."
            ),
            elapsed_sec=time.perf_counter() - context.started_at,
            progress_pct=round(((context.progress_index - 1) / context.total_pages) * 100.0, 1),
            remaining_pages=context.remaining_pages,
            completed_ai_pages=context.completed_ai_pages,
            completed_ai_duration_sec=context.completed_ai_duration_sec,
        )

        try:
            translated_page = self._translator.translate_scan(
                context.scan,
                custom_prompt=context.command.custom_prompt,
                target_language=context.command.target_language,
                source_language=context.command.source_language,
            )
            markdown_text = translated_page.markdown_content
            tok_per_sec = getattr(translated_page, "tokens_per_sec", 0.0)
            if not self._validator.validate_page_integrity(markdown_text):
                markdown_text = f"<!-- Ostrze\u017cenie walidacji strony -->\n{markdown_text}"
            self._page_repo.write_markdown(context.output_path, markdown_text)

            page_duration = max(time.perf_counter() - page_start_time, 0.01)
            completed_pages = context.completed_ai_pages + 1
            completed_duration = context.completed_ai_duration_sec + page_duration
            context.job.mark_page_completed(context.scan.page_number)
            self._emit_telemetry(
                context.job,
                current_page=int(context.scan.page_number),
                step_desc=(
                    f"\u2705 Uko\u0144czono stron\u0119 {int(context.scan.page_number)}/{context.total_pages} "
                    f"({page_duration:.1f}s, {tok_per_sec:.1f} tok/s)"
                ),
                page_duration_sec=page_duration,
                tokens_per_sec=tok_per_sec,
                elapsed_sec=time.perf_counter() - context.started_at,
                progress_pct=round((context.progress_index / context.total_pages) * 100.0, 1),
                remaining_pages=context.remaining_pages,
                completed_ai_pages=completed_pages,
                completed_ai_duration_sec=completed_duration,
            )
            return completed_pages, completed_duration
        except Exception as page_error:
            context.job.mark_page_failed(context.scan.page_number, str(page_error))
            self._emit_telemetry(
                context.job,
                current_page=int(context.scan.page_number),
                step_desc=(
                    f"\u274c B\u0142\u0105d strony {int(context.scan.page_number)}/{context.total_pages}: {page_error}"
                ),
                error_msg=str(page_error),
                progress_pct=round((context.progress_index / context.total_pages) * 100.0, 1),
                remaining_pages=context.remaining_pages,
                completed_ai_pages=context.completed_ai_pages,
                completed_ai_duration_sec=context.completed_ai_duration_sec,
            )
            return context.completed_ai_pages, context.completed_ai_duration_sec

    def _emit_telemetry(
        self,
        job: ConversionJob,
        current_page: int,
        step_desc: str,
        page_duration_sec: float = 0.0,
        tokens_per_sec: float = 0.0,
        elapsed_sec: float = 0.0,
        error_msg: Optional[str] = None,
        progress_pct: Optional[float] = None,
        remaining_pages: Optional[int] = None,
        completed_ai_pages: int = 0,
        completed_ai_duration_sec: float = 0.0,
    ) -> None:
        used_vram, total_vram, gpu_util = self._gpu.get_gpu_stats()
        progress = (
            progress_pct
            if progress_pct is not None
            else ((current_page / job.total_pages * 100.0) if job.total_pages > 0 else 0.0)
        )
        rem = remaining_pages if remaining_pages is not None else max(job.total_pages - current_page, 0)
        if completed_ai_pages > 0:
            average_page_duration = completed_ai_duration_sec / completed_ai_pages
        elif page_duration_sec > 0:
            average_page_duration = page_duration_sec
        else:
            average_page_duration = 0.0
        eta = rem * average_page_duration

        telemetry = ConversionTelemetry(
            task_id=job.task_id,
            book_slug=job.book_slug,
            state=job.state,
            current_page=current_page,
            total_pages=job.total_pages,
            progress_pct=min(max(progress, 0.0), 100.0),
            elapsed_sec=elapsed_sec,
            page_duration_sec=page_duration_sec,
            tokens_per_sec=tokens_per_sec,
            eta_sec=eta,
            vram_used_mb=used_vram,
            vram_total_mb=total_vram,
            gpu_utilization_pct=gpu_util,
            current_step_description=step_desc,
            error_message=error_msg,
        )
        self._broadcaster.broadcast(telemetry)
