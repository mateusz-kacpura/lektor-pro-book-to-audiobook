"""PDF splitter adapter converting document pages into 300 DPI JPG images."""

from pathlib import Path
from typing import Optional, Sequence

import pymupdf as fitz

from ...application.ports.ocr_ports import PdfSplitterProtocol
from ...domain.conversion_models import DocumentScan, create_page_number, format_page_filename


class PyMuPdfSplitterAdapter(PdfSplitterProtocol):
    """PDF splitter implementation using PyMuPDF (fitz)."""

    def get_page_count(self, pdf_path: Path) -> int:
        """Returns total number of pages in PDF document."""
        if not pdf_path.exists():
            raise FileNotFoundError(f"Plik PDF nie istnieje: {pdf_path}")

        doc = fitz.open(str(pdf_path))
        try:
            return len(doc)
        finally:
            doc.close()

    def render_page(
        self,
        pdf_path: Path,
        page_index_0based: int,
        output_path: Path,
        dpi: int = 300,
    ) -> None:
        """Renders a single page to a JPG file at 300 DPI."""
        if not pdf_path.exists():
            raise FileNotFoundError(f"Plik PDF nie istnieje: {pdf_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        doc = fitz.open(str(pdf_path))
        try:
            page = doc.load_page(page_index_0based)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            pix.save(str(output_path))
        finally:
            doc.close()

    def split_pdf(
        self,
        pdf_path: Path,
        output_dir: Path,
        dpi: int = 300,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
    ) -> Sequence[DocumentScan]:
        """Splits PDF into page images."""
        if not pdf_path.exists():
            raise FileNotFoundError(f"Plik PDF nie istnieje: {pdf_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(str(pdf_path))
        scans: list[DocumentScan] = []

        # Standard PDF has 72 points per inch. Scaling: zoom = dpi / 72.0
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        start_idx = (start_page - 1) if (start_page is not None and start_page >= 1) else 0
        end_idx = min(end_page, len(doc)) if (end_page is not None and end_page >= 1) else len(doc)

        try:
            for idx in range(start_idx, end_idx):
                page_idx_1based = idx + 1
                page_num = create_page_number(page_idx_1based)
                file_name = format_page_filename(page_num, prefix="page_", ext=".jpg")
                out_file_path = output_dir / file_name

                # Implementation note: see the surrounding code for the behavior described here.
                if out_file_path.exists() and out_file_path.stat().st_size > 0:
                    scans.append(DocumentScan(page_number=page_num, scan_path=out_file_path, dpi=dpi))
                    continue

                # Render page to RGB pixels
                page = doc.load_page(idx)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                pix.save(str(out_file_path))

                scans.append(DocumentScan(page_number=page_num, scan_path=out_file_path, dpi=dpi))
        finally:
            doc.close()

        return tuple(scans)
