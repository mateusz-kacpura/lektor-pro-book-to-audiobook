"""
lektor.application.dtos
~~~~~~~~~~~~~~~~~~~~~~~
Data Transfer Objects (DTO) for Use Cases.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence

from ..domain.audio_models import CodeMode, LanguageMode, SpeechSegment
from ..domain.conversion_models import BookSlug, ConversionTaskId
from ..domain.languages import LanguagePair


@dataclass(frozen=True)
class SynthesizePageCommand:
    """Input parameters for single page synthesis use case."""

    markdown_path: Path
    output_dir: Path
    skip_existing: bool = False
    save_normalized_text: bool = True
    audio_format: str = "wav"
    language_pair: LanguagePair | None = None


@dataclass(frozen=True)
class BatchSynthesisCommand:
    """Input parameters for batch book synthesis."""

    pages_dir: Path
    output_dir: Path
    pattern: str = "page_*.md"
    skip_existing: bool = True
    save_normalized_text: bool = True
    audio_format: str = "wav"
    language_pair: LanguagePair | None = None


@dataclass(frozen=True)
class PreviewPageQuery:
    """Input parameters for page normalization preview query."""

    markdown_path: Optional[Path] = None
    raw_text: Optional[str] = None
    code_mode: CodeMode = "spoken"
    language_mode: LanguageMode = "bilingual"
    language_pair: LanguagePair | None = None


@dataclass(frozen=True)
class PreviewPageResult:
    """Result of text normalization preview query."""

    segments: Sequence[SpeechSegment]
    total_chars: int
    total_words: int
    segment_count: int
    pl_segments_count: int
    en_segments_count: int
    formatted_preview: str


@dataclass(frozen=True)
class ConvertBookCommand:
    """Input parameters for book conversion use case (OCR to Markdown)."""

    input_dir: Path
    output_dir: Path
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    overwrite: bool = False
    timeout_sec: int = 360
    batch_size: int = 4
    target_language: str = "pl"
    source_language: Optional[str] = None


@dataclass(frozen=True)
class ConvertBookResult:
    """Summary of book conversion."""

    total_pages_found: int
    processed_count: int
    skipped_count: int
    failed_pages: Sequence[tuple[int, str]] = field(default_factory=tuple)
    duration_sec: float = 0.0


@dataclass(frozen=True)
class SynthesizeSnippetCommand:
    """Input parameters for synthesizing a single Markdown text snippet (Studio)."""

    snippet_id: str
    markdown: str
    output_path: Path
    language_mode: LanguageMode = "bilingual"
    language_pair: LanguagePair | None = None
    force: bool = False
    voice_path: Optional[Path] = None
    temperature: float = 0.35
    cfg_weight: float = 0.7
    audio_format: str = "wav"


@dataclass(frozen=True)
class SynthesizeSnippetResult:
    """Result of Markdown snippet synthesis."""

    snippet_id: str
    audio_path: Path
    duration_sec: float
    file_size_kb: float
    segment_count: int
    normalized_preview: Sequence[str]
    skipped_existing: bool = False


# ============================================================================
# Implementation note: see the surrounding code for the behavior described here.
# ============================================================================


@dataclass(frozen=True)
class StartConversionCommand:
    """Parameters for starting a PDF conversion task."""

    pdf_path: Path
    book_slug: BookSlug
    dpi: int = 300
    target_language: str = "pl"
    source_language: Optional[str] = None
    custom_prompt: Optional[str] = None
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    skip_existing: bool = True
    scans_dir: Optional[Path] = None
    pages_dir: Optional[Path] = None


@dataclass(frozen=True)
class CancelConversionCommand:
    """Request to cancel a conversion task."""

    task_id: ConversionTaskId


@dataclass(frozen=True)
class SwitchActiveBookCommand:
    """Command to switch the current active book."""

    slug: BookSlug


@dataclass(frozen=True)
class BookMetadataDTO:
    """Book metadata exposed to the Web GUI interface."""

    slug: str
    title: str
    total_pages: int
    audio_pages: int
    scan_pages: int
    is_active: bool


@dataclass(frozen=True)
class RenderScansStreamCommand:
    """Input parameters for streaming PDF scans rendering."""

    book_slug: str
    dpi: int = 300
    start_page: Optional[int] = None
    end_page: Optional[int] = None


@dataclass(frozen=True)
class RenderScansCommand:
    """Input parameters for synchronous PDF scans rendering."""

    book_slug: str
    dpi: int = 300
    start_page: Optional[int] = None
    end_page: Optional[int] = None


@dataclass(frozen=True)
class RenderScansResultDTO:
    """Result of rendering book page scans from PDF."""

    book_slug: str
    scans_created: int
    scans_dir: str
    total_scans: int
    message: str


@dataclass(frozen=True)
class GetBookStatusQuery:
    """Input parameters for querying aggregated book and player status."""

    book_slug: Optional[str] = None


@dataclass(frozen=True)
class PageStatusDTO:
    """Information about a single page in the player."""

    id: str
    filename: str
    title: str
    status: str
    has_wav: bool
    has_txt: bool
    duration: float
    duration_str: str


@dataclass(frozen=True)
class BookStatusDTO:
    """Aggregated status of active book and player."""

    book_title: str
    total_pdf_pages: int
    markdown_pages_count: int
    is_batch_running: bool
    is_stopping: bool
    total_pages: int
    ready_count: int
    latest_ready_page: Optional[str]
    active_generation: Optional[str]
    progress: dict[str, object]
    current_params: dict[str, object]
    available_voices: list[dict[str, str]]
    pages: list[dict[str, object]]
