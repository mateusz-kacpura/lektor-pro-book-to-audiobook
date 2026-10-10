"""
lektor.application.ports.ocr_ports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Input/output ports for Markdown formatting, PDF splitting, and AI Vision OCR models.
Strict typing without Any.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol, Sequence

from ...domain.book_models import PageNumber
from ...domain.conversion_models import DocumentScan, TranslatedMarkdownPage


class BookMarkdownFormatterProtocol(Protocol):
    """Abstract contract for output Markdown formatter with page metadata."""

    def format_markdown(
        self,
        raw_md: str,
        page_num: PageNumber,
        img_name: str,
        book_dir_name: str = "scans",
    ) -> str:
        """Formats raw Markdown text with page metadata header."""
        ...


class PdfSplitterProtocol(Protocol):
    """Abstract contract for splitting PDF files into page images (DPI 300)."""

    def split_pdf(
        self,
        pdf_path: Path,
        output_dir: Path,
        dpi: int = 300,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
    ) -> Sequence[DocumentScan]:
        """Splits PDF file into sequential JPG page images."""
        ...

    def get_page_count(self, pdf_path: Path) -> int:
        """Returns total number of pages in the PDF document."""
        ...

    def render_page(
        self,
        pdf_path: Path,
        page_index_0based: int,
        output_path: Path,
        dpi: int = 300,
    ) -> None:
        """Renders a single PDF document page to an image file."""
        ...


@dataclass(frozen=True)
class VisionApiResponse:
    """Immutable response from multimodal API client."""
    raw_content: str
    tokens_per_sec: float
    total_tokens: int
    duration_sec: float


class VisionApiClientProtocol(Protocol):
    """Abstract contract for multimodal vision API client."""

    @property
    def model_name(self) -> str:
        """Name or identifier of the active model."""
        ...

    def send_vision_request(
        self,
        image_bytes: bytes,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> VisionApiResponse:
        """Sends image and prompts to vision model and returns structured response."""
        ...


class VisionPromptBuilderProtocol(Protocol):
    """Abstract contract for vision model translation prompt builder."""

    def build_system_prompt(
        self,
        target_language: str = "pl",
        source_language: Optional[str] = None,
    ) -> str:
        """Creates system prompt defining translator role and language rules."""
        ...

    def build_user_prompt(
        self,
        target_language: str = "pl",
        source_language: Optional[str] = None,
        custom_instructions: Optional[str] = None,
    ) -> str:
        """Creates user request prompt for a single page."""
        ...


class VisionTranslatorProtocol(Protocol):
    """Abstract contract for AI Vision orchestrator (translation, code, and Mermaid)."""

    def translate_scan(
        self,
        scan: DocumentScan,
        custom_prompt: Optional[str] = None,
        target_language: str = "pl",
        source_language: Optional[str] = None,
    ) -> TranslatedMarkdownPage:
        """Analyzes page scan, translates content, preserves code, and generates Mermaid."""
        ...