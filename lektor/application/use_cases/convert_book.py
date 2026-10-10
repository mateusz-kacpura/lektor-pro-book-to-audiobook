"""
lektor.application.use_cases.convert_book
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use case: Converting page scans (JPG/PNG) to Markdown using Vision AI (Qwen2.5-VL:7B).
Orchestrates multimodal recognition, formatting, and saving to Markdown.
"""

import re
import time
from pathlib import Path
from typing import Optional

from ...domain.conversion_models import DocumentScan, PageNumber, create_page_number
from ..dtos import ConvertBookCommand, ConvertBookResult
from ..ports.ocr_ports import BookMarkdownFormatterProtocol, VisionTranslatorProtocol
from ..ports.storage_ports import PageRepositoryProtocol
from ..ports.telemetry_ports import ProgressReporterProtocol


class ConvertBookUseCase:
    """
    Orchestrates batch conversion of book scans to formatted Markdown files
    using exclusively the Qwen2.5-VL:7B model.
    """

    def __init__(
        self,
        vision_translator: VisionTranslatorProtocol,
        markdown_formatter: BookMarkdownFormatterProtocol,
        page_repository: PageRepositoryProtocol,
        progress_reporter: Optional[ProgressReporterProtocol] = None,
    ) -> None:
        self._translator = vision_translator
        self._formatter = markdown_formatter
        self._repo = page_repository
        self._reporter = progress_reporter

    def execute(self, cmd: ConvertBookCommand) -> ConvertBookResult:
        """Executes batch vision analysis of book pages."""
        images = self._get_sorted_images(cmd.input_dir)
        total_found = len(images)

        if cmd.start_page is not None:
            images = [img for img in images if img[0] >= cmd.start_page]
        if cmd.end_page is not None:
            images = [img for img in images if img[0] <= cmd.end_page]

        to_process: list[tuple[int, Path, Path]] = []
        for page_num, img_path in images:
            out_file = cmd.output_dir / f"page_{page_num:03d}.md"
            if out_file.exists() and not cmd.overwrite:
                try:
                    if out_file.stat().st_size > 50:
                        continue
                except OSError:
                    pass
            to_process.append((page_num, img_path, out_file))

        processed_count = 0
        skipped_count = total_found - len(to_process)
        failed_pages: list[tuple[int, str]] = []
        t_start = time.time()

        for idx, (page_num, img_path, out_file) in enumerate(to_process, 1):
            if self._reporter and self._reporter.check_cancellation():
                break

            scan = DocumentScan(page_number=create_page_number(page_num), scan_path=img_path)
            try:
                translated_page = self._translator.translate_scan(scan)
                formatted_md = self._formatter.format_markdown(
                    raw_md=translated_page.markdown_content,
                    page_num=PageNumber(page_num),
                    img_name=img_path.name,
                    book_dir_name=cmd.input_dir.name,
                )
                self._repo.write_markdown(out_file, formatted_md)
                processed_count += 1
            except Exception as err:
                failed_pages.append((page_num, str(err)))
                skipped_count += 1

        total_duration = time.time() - t_start

        return ConvertBookResult(
            total_pages_found=total_found,
            processed_count=processed_count,
            skipped_count=skipped_count,
            failed_pages=failed_pages,
            duration_sec=total_duration,
        )

    def _get_sorted_images(self, input_dir: Path) -> list[tuple[int, Path]]:
        """Discovers and sorts page scan files by page number."""
        pattern = re.compile(r"page[-_]?(\d+)\.(jpg|jpeg|png)$", re.IGNORECASE)
        images: list[tuple[int, Path]] = []
        if not input_dir.exists():
            return images

        for f in input_dir.iterdir():
            if f.is_file():
                m = pattern.search(f.name)
                if m:
                    images.append((int(m.group(1)), f))

        images.sort(key=lambda x: x[0])
        return images
