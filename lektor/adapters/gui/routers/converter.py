"""
lektor.adapters.gui.routers.converter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
FastAPI router for dynamic book management and PDF conversion with live SSE telemetry.
Clean Architecture compliant. Strict typing without Any.
"""

import asyncio
import json
import threading
from pathlib import Path
from typing import AsyncIterator, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ....application.dtos import (
    BookMetadataDTO,
    RenderScansCommand,
    RenderScansStreamCommand,
    StartConversionCommand,
    SwitchActiveBookCommand,
)
from ....application.ports.ocr_ports import PdfSplitterProtocol
from ....application.ports.storage_ports import BookRepositoryProtocol
from ....application.ports.telemetry_ports import TelemetryBroadcasterProtocol
from ....application.use_cases.convert_pdf_book import ConvertPdfBookUseCase
from ....application.use_cases.import_pdf_book import ImportPdfBookCommand, ImportPdfBookUseCase
from ....application.use_cases.list_books import ListBooksUseCase
from ....application.use_cases.render_pdf_scans import RenderPdfScansUseCase
from ....application.use_cases.render_scans_stream import RenderPdfScansStreamUseCase
from ....application.use_cases.switch_active_book import SwitchActiveBookUseCase
from ....domain.conversion_models import (
    ConversionJob,
    ConversionTaskId,
    validate_book_slug,
)
from ..container import ApplicationContainerProtocol
from ..dependencies import (
    get_book_repository,
    get_container,
    get_convert_pdf_book_use_case,
    get_import_pdf_book_use_case,
    get_list_books_use_case,
    get_pdf_splitter,
    get_render_pdf_scans_use_case,
    get_render_scans_stream_use_case,
    get_switch_active_book_use_case,
    get_telemetry_broadcaster,
)
from ..schemas.converter_schemas import (
    BookPdfInfoResponse,
    RenderScansRequest,
    RenderScansResponse,
    StartConversionRequest,
    StartConversionResponse,
    SwitchBookRequest,
)

router = APIRouter(prefix="/api", tags=["converter"])

_active_jobs: dict[str, ConversionJob] = {}
_active_conversion_threads: dict[str, threading.Thread] = {}


def wait_for_conversion_tasks() -> None:
    """Waits for active conversion tasks to finish before releasing AI models."""
    for thread in tuple(_active_conversion_threads.values()):
        thread.join()


@router.get("/books", response_model=list[BookMetadataDTO])
def get_books_list(
    uc: ListBooksUseCase = Depends(get_list_books_use_case),
) -> list[BookMetadataDTO]:
    """Returns list of all books in storage with metadata and statistics."""
    return list(uc.execute())


@router.post("/active-book", response_model=BookMetadataDTO)
def switch_active_book(
    req: SwitchBookRequest,
    uc: SwitchActiveBookUseCase = Depends(get_switch_active_book_use_case),
    container: ApplicationContainerProtocol = Depends(get_container),
) -> BookMetadataDTO:
    """Dynamically switches the active book in application memory."""
    try:
        slug = validate_book_slug(req.slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    res = uc.execute(SwitchActiveBookCommand(slug=slug))
    container.reset_book_context()
    return res


@router.get("/converter/info/{slug}", response_model=BookPdfInfoResponse)
def get_converter_book_info(
    slug: str,
    book_repo: BookRepositoryProtocol = Depends(get_book_repository),
    pdf_splitter: PdfSplitterProtocol = Depends(get_pdf_splitter),
) -> BookPdfInfoResponse:
    """Returns information about PDF file, scans, and Markdown pages for selected book."""
    try:
        clean_slug = validate_book_slug(slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    book = book_repo.get_book(clean_slug)
    if not book:
        raise HTTPException(status_code=404, detail=f"Książka '{slug}' nie istnieje w magazynie.")

    pdf_file = book.paths.original_pdf
    pdf_path_str: Optional[str] = str(pdf_file) if (pdf_file and pdf_file.exists()) else None

    pages_count = len(list(book.paths.pages_dir.glob("page_*.md"))) if book.paths.pages_dir.exists() else 0

    actual_pdf_pages = 0
    if pdf_file and pdf_file.exists():
        try:
            actual_pdf_pages = pdf_splitter.get_page_count(pdf_file)
        except Exception:
            actual_pdf_pages = book.metadata.total_pages or 0
    else:
        actual_pdf_pages = book.metadata.total_pages or 0

    scans_count = len(book_repo.get_existing_scans(str(clean_slug)))
    if actual_pdf_pages > 0:
        scans_count = min(scans_count, actual_pdf_pages)

    return BookPdfInfoResponse(
        book_slug=str(clean_slug),
        title=book.metadata.title,
        pdf_path=pdf_path_str,
        pdf_exists=bool(pdf_file and pdf_file.exists()),
        pages_count=pages_count,
        scans_count=scans_count,
        total_pages=actual_pdf_pages if actual_pdf_pages > 0 else (scans_count if scans_count > 0 else 0),
        language=book.metadata.language or "pl",
    )


@router.post("/converter/import-pdf", response_model=BookPdfInfoResponse)
async def import_pdf_book(
    file: UploadFile = File(..., description="Plik PDF do zaimportowania"),
    title: Optional[str] = Form(default=None, description="Opcjonalny tytuł książki"),
    author: Optional[str] = Form(default=None, description="Opcjonalny autor książki"),
    slug: Optional[str] = Form(default=None, description="Opcjonalny unikalny slug książki"),
    uc: ImportPdfBookUseCase = Depends(get_import_pdf_book_use_case),
) -> BookPdfInfoResponse:
    """Imports PDF file into the dedicated book storage directory."""
    filename = file.filename or "imported_book.pdf"
    contents = await file.read()

    try:
        cmd = ImportPdfBookCommand(
            file_bytes=contents,
            filename=filename,
            title=title,
            author=author,
            slug=slug,
        )
        res = uc.execute(cmd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return BookPdfInfoResponse(
        book_slug=res.book.slug,
        title=res.book.title,
        pdf_path=str(res.pdf_path),
        pdf_exists=True,
        pages_count=0,
        scans_count=0,
        total_pages=res.total_pages,
        language=res.book.metadata.language or "pl",
    )


@router.post("/converter/render-scans", response_model=RenderScansResponse)
def render_pdf_scans(
    req: RenderScansRequest,
    uc: RenderPdfScansUseCase = Depends(get_render_pdf_scans_use_case),
) -> RenderScansResponse:
    """Renders PDF scans into the book scans/ directory at 300 DPI."""
    try:
        cmd = RenderScansCommand(
            book_slug=req.book_slug,
            dpi=req.dpi,
            start_page=req.start_page,
            end_page=req.end_page,
        )
        res = uc.execute(cmd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return RenderScansResponse(
        book_slug=res.book_slug,
        scans_created=res.scans_created,
        scans_dir=res.scans_dir,
        total_scans=res.total_scans,
        message=res.message,
    )


@router.get("/converter/render-scans-stream")
async def render_pdf_scans_stream(
    slug: str,
    dpi: int = 300,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
    book_repo: BookRepositoryProtocol = Depends(get_book_repository),
    uc: RenderPdfScansStreamUseCase = Depends(get_render_scans_stream_use_case),
) -> StreamingResponse:
    """Renders PDF pages to JPG format (300 DPI) and streams live progress via SSE."""
    try:
        clean_slug = validate_book_slug(slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    book = book_repo.get_book(clean_slug)
    if not book:
        raise HTTPException(status_code=404, detail=f"Książka '{clean_slug}' nie istnieje.")

    pdf_file = book.paths.original_pdf
    if not pdf_file or not pdf_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"W katalogu książki '{clean_slug}' nie znaleziono pliku PDF.",
        )

    cmd = RenderScansStreamCommand(
        book_slug=str(clean_slug),
        dpi=dpi,
        start_page=start_page,
        end_page=end_page,
    )

    async def event_generator() -> AsyncIterator[str]:
        try:
            async for event_data in uc.execute_stream(cmd):
                yield f"data: {json.dumps(event_data)}\n\n"
        except (ValueError, FileNotFoundError) as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/converter/start", response_model=StartConversionResponse)
def start_conversion(
    req: StartConversionRequest,
    uc: ConvertPdfBookUseCase = Depends(get_convert_pdf_book_use_case),
    container: ApplicationContainerProtocol = Depends(get_container),
) -> StartConversionResponse:
    """Starts background PDF conversion task for the selected target language."""
    try:
        slug = validate_book_slug(req.book_slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    pdf_file = Path(req.pdf_path).resolve()
    if not pdf_file.exists():
        raise HTTPException(status_code=404, detail=f"Plik PDF nie istnieje: {pdf_file}")

    job = ConversionJob.create(book_slug=slug, pdf_path=pdf_file)
    task_id_str = str(job.task_id)
    _active_jobs[task_id_str] = job

    cmd = StartConversionCommand(
        pdf_path=pdf_file,
        book_slug=slug,
        dpi=req.dpi,
        target_language=req.target_language.strip().lower() or "pl",
        source_language=req.source_language.strip().lower() if req.source_language else None,
        custom_prompt=req.custom_prompt,
        start_page=req.start_page,
        end_page=req.end_page,
        skip_existing=req.skip_existing,
    )

    active_uc = container.create_convert_pdf_book_use_case(model_name=req.model_name) if req.model_name else uc
    worker = threading.Thread(
        target=active_uc.execute,
        args=(cmd, job),
        name=f"pdf-conversion-{task_id_str}",
        daemon=False,
    )
    _active_conversion_threads[task_id_str] = worker
    worker.start()

    return StartConversionResponse(
        task_id=task_id_str,
        status="started",
        message=f"Rozpoczęto zadanie konwersji PDF dla książki '{slug}' (język docelowy: {cmd.target_language})",
    )


@router.post("/converter/cancel/{task_id}")
def cancel_conversion(task_id: str) -> dict[str, str]:
    """Sends cancellation signal to the active conversion task."""
    job = _active_jobs.get(task_id)
    if not job:
        raise HTTPException(status_code=404, detail="Zadanie o podanym ID nie istnieje")

    job.request_cancellation()
    return {"task_id": task_id, "status": "cancellation_requested"}


@router.get("/converter/progress/{task_id}")
async def get_conversion_progress(
    task_id: str,
    broadcaster: TelemetryBroadcasterProtocol = Depends(get_telemetry_broadcaster),
) -> StreamingResponse:
    """Streams real-time progress telemetry via Server-Sent Events (SSE)."""
    typed_task_id = ConversionTaskId(task_id)

    async def event_generator() -> AsyncIterator[str]:
        async for telemetry in broadcaster.subscribe(typed_task_id):
            payload = {
                "task_id": str(telemetry.task_id),
                "book_slug": str(telemetry.book_slug),
                "state": str(telemetry.state),
                "current_page": telemetry.current_page,
                "total_pages": telemetry.total_pages,
                "progress_pct": round(telemetry.progress_pct, 1),
                "elapsed_sec": round(telemetry.elapsed_sec, 1),
                "page_duration_sec": round(telemetry.page_duration_sec, 2),
                "tokens_per_sec": round(telemetry.tokens_per_sec, 1),
                "eta_sec": round(telemetry.eta_sec, 1),
                "vram_used_mb": round(telemetry.vram_used_mb, 1),
                "vram_total_mb": round(telemetry.vram_total_mb, 1),
                "gpu_utilization_pct": round(telemetry.gpu_utilization_pct, 1),
                "current_step_description": telemetry.current_step_description,
                "error_message": telemetry.error_message,
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(0.05)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )