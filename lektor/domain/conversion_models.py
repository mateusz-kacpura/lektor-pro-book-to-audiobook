"""
lektor.domain.conversion_models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Entities and Value Objects for the PDF conversion pipeline,
AI vision translation, and real-time telemetry.
Strict typing without Any (Python 3.14+).
"""

import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import NewType, Optional
from uuid import UUID, uuid4

from .book_models import PageNumber as PageNumber
from .book_models import create_page_number as create_page_number

# --- Strongly typed identifiers (NewType) ---
BookSlug = NewType("BookSlug", str)
ConversionTaskId = NewType("ConversionTaskId", str)


def validate_book_slug(value: str) -> BookSlug:
    """
    Validates book slug according to Business Rule 1:
    must consist exclusively of lowercase letters, digits, and underscores.
    """
    clean = value.strip().lower()
    if not re.match(r"^[a-z0-9_]+$", clean):
        raise ValueError(
            f"NieprawidĹ‚owy slug ksiÄ…ĹĽki '{value}'. Dozwolone sÄ… wyĹ‚Ä…cznie maĹ‚e litery, cyfry i znak '_'."
        )
    return BookSlug(clean)


def to_book_slug(text: str) -> BookSlug:
    """Converts arbitrary text (e.g. title or filename) to a validated BookSlug (SSOT)."""
    clean = text.lower().strip()
    clean = re.sub(r"[^\w\s-]", "", clean)
    clean = re.sub(r"[\s_-]+", "_", clean)
    return validate_book_slug(clean or "book")


def format_page_filename(page_num: PageNumber, prefix: str = "page_", ext: str = ".jpg", digits: int = 3) -> str:
    """Formats page filename with fixed zero padding (e.g. page_042.jpg)."""
    return f"{prefix}{int(page_num):0{digits}d}{ext}"


class ConversionTaskState(StrEnum):
    """Lifecycle states of a conversion task (Business Rule 10)."""
    IDLE = "IDLE"
    SPLITTING_PDF = "SPLITTING_PDF"
    TRANSLATING = "TRANSLATING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class DocumentScan:
    """Value Object representing a rendered single page scan."""
    page_number: PageNumber
    scan_path: Path
    dpi: int = 300


@dataclass(frozen=True)
class MermaidDiagram:
    """Value Object representing a flowchart transcribed into Mermaid.js."""
    raw_code: str
    diagram_type: str = "flowchart"
    title: str = ""


MERMAID_DIAGRAM_KEYWORDS: tuple[str, ...] = (
    "flowchart",
    "graph",
    "sequencediagram",
    "classdiagram",
    "statediagram",
    "erdiagram",
    "gantt",
    "pie",
    "gitgraph",
    "c4context",
    "c4container",
    "c4component",
    "architecture-beta",
)


@dataclass(frozen=True)
class TranslatedMarkdownPage:
    """Value Object representing a translated Markdown page with code and diagrams preserved."""
    page_number: PageNumber
    markdown_content: str
    diagrams: tuple[MermaidDiagram, ...] = ()
    code_blocks_count: int = 0
    tokens_per_sec: float = 0.0

    @classmethod
    def from_raw_markdown(
        cls,
        page_number: PageNumber,
        raw_markdown: str,
        tokens_per_sec: float = 0.0,
    ) -> "TranslatedMarkdownPage":
        """
        Domain factory method: cleans surrounding Markdown tags,
        detects Mermaid diagrams, and counts code blocks.
        """
        clean_md = raw_markdown.strip()
        if clean_md.startswith("```markdown\n") and clean_md.endswith("```"):
            clean_md = clean_md[len("```markdown\n") : -3].strip()
        elif clean_md.startswith("```md\n") and clean_md.endswith("```"):
            clean_md = clean_md[len("```md\n") : -3].strip()

        # Implementation note: see the surrounding code for the behavior described here.
        mermaid_blocks = re.findall(r"```mermaid\n(.*?)```", clean_md, re.DOTALL | re.IGNORECASE)
        diagrams: list[MermaidDiagram] = []
        for idx, block in enumerate(mermaid_blocks, start=1):
            clean_code = block.strip()
            first_line = clean_code.splitlines()[0].strip().lower() if clean_code else ""
            dtype = "flowchart"
            for kw in MERMAID_DIAGRAM_KEYWORDS:
                if first_line.startswith(kw):
                    dtype = kw
                    break
            diagrams.append(
                MermaidDiagram(
                    raw_code=clean_code,
                    diagram_type=dtype,
                    title=f"Diagram strona {int(page_number)} ({idx})",
                )
            )

        # Implementation note: see the surrounding code for the behavior described here.
        code_blocks = re.findall(r"```[a-zA-Z0-9_-]*\n(.*?)```", clean_md, re.DOTALL)
        code_count = len(code_blocks) - len(mermaid_blocks)

        return cls(
            page_number=page_number,
            markdown_content=clean_md,
            diagrams=tuple(diagrams),
            code_blocks_count=max(code_count, 0),
            tokens_per_sec=tokens_per_sec,
        )


@dataclass(frozen=True)
class ConversionTelemetry:
    """Real-time telemetry Value Object (Business Rule 11)."""
    task_id: ConversionTaskId
    book_slug: BookSlug
    state: ConversionTaskState
    current_page: int
    total_pages: int
    progress_pct: float
    elapsed_sec: float
    page_duration_sec: float
    tokens_per_sec: float
    eta_sec: float
    vram_used_mb: float
    vram_total_mb: float
    gpu_utilization_pct: float
    current_step_description: str
    error_message: Optional[str] = None


@dataclass
class ConversionJob:
    """Entity representing the state and lifecycle of a book conversion task."""
    task_id: ConversionTaskId
    book_slug: BookSlug
    pdf_path: Path
    state: ConversionTaskState = ConversionTaskState.IDLE
    total_pages: int = 0
    completed_pages: int = 0
    failed_pages: dict[int, str] = field(default_factory=dict)
    cancellation_requested: bool = False
    pause_requested: bool = False

    @classmethod
    def create(cls, book_slug: BookSlug, pdf_path: Path) -> "ConversionJob":
        task_uuid: UUID = uuid4()
        return cls(
            task_id=ConversionTaskId(str(task_uuid)),
            book_slug=book_slug,
            pdf_path=pdf_path,
        )

    def transition_to(self, new_state: ConversionTaskState) -> None:
        """Transitions the job state machine to a new state."""
        self.state = new_state

    def mark_page_completed(self, page_num: PageNumber) -> None:
        self.completed_pages += 1
        page_val = int(page_num)
        if page_val in self.failed_pages:
            del self.failed_pages[page_val]

    def mark_page_failed(self, page_num: PageNumber, error_msg: str) -> None:
        self.failed_pages[int(page_num)] = error_msg

    def request_cancellation(self) -> None:
        self.cancellation_requested = True

    def request_pause(self) -> None:
        self.pause_requested = True

    def resume(self) -> None:
        self.pause_requested = False

    def is_terminal(self) -> bool:
        return self.state in (
            ConversionTaskState.COMPLETED,
            ConversionTaskState.CANCELLED,
            ConversionTaskState.FAILED,
        )
