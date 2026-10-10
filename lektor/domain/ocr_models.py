"""
lektor.domain.ocr_models
~~~~~~~~~~~~~~~~~~~~~~~~
Value Objects for OCR image extraction results and page layout analysis.
Strict typing without Any.
"""

from dataclasses import dataclass, field
from typing import Sequence

from .audio_models import PageNumber


@dataclass(frozen=True)
class OCRBlockResult:
    """Extracted layout block from a page image by the OCR model."""
    block_type: str  # e.g. 'text', 'table', 'code', 'image'
    content: str


@dataclass(frozen=True)
class OCRPageResult:
    """Complete OCR page extraction result with layout and text blocks."""
    page_number: PageNumber
    raw_markdown: str
    formatted_markdown: str
    blocks: Sequence[OCRBlockResult] = field(default_factory=tuple)
    duration_sec: float = 0.0
    error: str | None = None
