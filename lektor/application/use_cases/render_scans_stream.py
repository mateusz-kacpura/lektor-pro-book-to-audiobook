"""
lektor.application.use_cases.render_scans_stream
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use case: Streaming rendering of PDF pages to 300 DPI JPG scans (SSE).
Orchestrates rendering loop, progress calculation, ETA, and event formatting.
Strict typing without Any.
"""

import asyncio
import time
from typing import AsyncIterator

from ...domain.conversion_models import create_page_number, format_page_filename, validate_book_slug
from ..dtos import RenderScansStreamCommand
from ..ports.ocr_ports import PdfSplitterProtocol
from ..ports.storage_ports import BookRepositoryProtocol


class RenderPdfScansStreamUseCase:
    """
    Use case asynchronously orchestrating PDF page rendering
    and generating progress events (SSE stream events).
    """

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        pdf_splitter: PdfSplitterProtocol,
    ) -> None:
        self._book_repo = book_repository
        self._pdf_splitter = pdf_splitter

    async def execute_stream(self, cmd: RenderScansStreamCommand) -> AsyncIterator[dict[str, object]]:
        clean_slug = validate_book_slug(cmd.book_slug)
        book = self._book_repo.get_book(clean_slug)
        if not book:
            raise ValueError(f"Książka '{clean_slug}' nie istnieje.")

        pdf_file = book.paths.original_pdf
        if not pdf_file or not pdf_file.exists():
            for candidate in book.paths.root_dir.glob("*.pdf"):
                pdf_file = candidate
                break

        if not pdf_file or not pdf_file.exists():
            raise FileNotFoundError(f"W katalogu książki '{clean_slug}' nie znaleziono pliku PDF.")

        total_in_doc = self._pdf_splitter.get_page_count(pdf_file)
        start_idx = (cmd.start_page - 1) if (cmd.start_page is not None and cmd.start_page >= 1) else 0
        end_idx = min(cmd.end_page, total_in_doc) if (cmd.end_page is not None and cmd.end_page >= 1) else total_in_doc
        total_to_render = max(1, end_idx - start_idx)


        yield {
            "status": "started",
            "total_pages": total_in_doc,
            "to_render": total_to_render,
            "start_page": start_idx + 1,
            "end_page": end_idx,
        }
        await asyncio.sleep(0.01)

        def _render_page_worker(p_idx: int, p_1based: int) -> tuple[str, str]:
            page_num = create_page_number(p_1based)
            file_name = format_page_filename(page_num, prefix="page_", ext=".jpg")
            out_path = book.paths.scans_dir / file_name
            self._pdf_splitter.render_page(
                pdf_path=pdf_file,
                page_index_0based=p_idx,
                output_path=out_path,
                dpi=cmd.dpi,
            )
            return file_name, str(out_path)

        rendered_count = 0
        t0 = time.perf_counter()

        for idx in range(start_idx, end_idx):
            page_1based = idx + 1
            file_name, _ = await asyncio.to_thread(_render_page_worker, idx, page_1based)

            rendered_count += 1
            elapsed = time.perf_counter() - t0
            pct = round((rendered_count / total_to_render) * 100.0, 1)
            speed = round(rendered_count / max(0.01, elapsed), 2)
            eta = round((total_to_render - rendered_count) / max(0.1, speed), 1)

            yield {
                "status": "rendering",
                "current_page": page_1based,
                "rendered_count": rendered_count,
                "total_to_render": total_to_render,
                "percent": pct,
                "file_name": file_name,
                "elapsed_sec": round(elapsed, 1),
                "speed_pages_per_sec": speed,
                "eta_sec": eta,
            }
            await asyncio.sleep(0.005)

        total_scans_on_disk = len(self._book_repo.get_existing_scans(str(clean_slug)))
        yield {
            "status": "completed",
            "total_scans": total_scans_on_disk,
            "rendered_count": rendered_count,
            "percent": 100.0,
            "message": f"Pomyślnie wyrenderowano {rendered_count} skanów w {cmd.dpi} DPI!",
        }
