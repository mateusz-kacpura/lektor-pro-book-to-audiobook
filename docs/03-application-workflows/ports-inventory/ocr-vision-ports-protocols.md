# OCR & vision ports & protocols

## Overview

This specification details port contracts governing document rasterization, Markdown formatting, multimodal API requests, and vision translation orchestration. Located in `lektor.application.ports.ocr_ports`.

---

## 1. `PdfSplitterProtocol`

Insulates the application from low-level PDF rendering engines:

```python
class PdfSplitterProtocol(Protocol):
    def split_pdf(
        self,
        pdf_path: Path,
        output_dir: Path,
        dpi: int = 300,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
    ) -> Sequence[DocumentScan]:
        """Renders sequential PDF pages into high-resolution JPEG bitmaps."""
        ...

    def get_page_count(self, pdf_path: Path) -> int:
        """Returns the total number of pages in the PDF document."""
        ...

    def render_page(
        self,
        pdf_path: Path,
        page_index_0based: int,
        output_path: Path,
        dpi: int = 300,
    ) -> None:
        """Renders a single 0-indexed page to a destination bitmap file."""
        ...

```

---

## 2. `VisionApiClientProtocol` & `VisionApiResponse`

Defines transport communication with local or remote OpenAI-compatible multimodal endpoints:

```python
@dataclass(frozen=True)
class VisionApiResponse:
    raw_content: str
    tokens_per_sec: float
    total_tokens: int
    duration_sec: float

class VisionApiClientProtocol(Protocol):
    @property
    def model_name(self) -> str:
        """Identifier of the active multimodal model."""
        ...

    def send_vision_request(
        self,
        image_bytes: bytes,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> VisionApiResponse:
        """Transmits image bytes and prompts, returning structured API metrics."""
        ...

```

---

## 3. `VisionPromptBuilderProtocol`

Encapsulates prompt construction for translation and code preservation:

```python
class VisionPromptBuilderProtocol(Protocol):
    def build_system_prompt(self) -> str:
        """Creates the system prompt establishing technical translation persona."""
        ...

    def build_user_prompt(self, custom_instructions: Optional[str] = None) -> str:
        """Creates the per-page user prompt instructing code and diagram preservation."""
        ...

```

---

## 4. `VisionTranslatorProtocol`

Orchestrates end-to-end scan interpretation, diagram detection, and code safety:

```python
class VisionTranslatorProtocol(Protocol):
    def translate_scan(
        self,
        scan: DocumentScan,
        custom_prompt: Optional[str] = None,
    ) -> TranslatedMarkdownPage:
        """Translates scanned bitmap, protects source code, and outputs a domain page."""
        ...

```

---

## 5. `BookMarkdownFormatterProtocol`

Formats extracted Markdown with JSON comment headers and scan link footers:

```python
class BookMarkdownFormatterProtocol(Protocol):
    def format_markdown(
        self,
        raw_md: str,
        page_num: PageNumber,
        img_name: str,
        book_dir_name: str = "scans",
    ) -> str:
        """Enriches raw Markdown with structured metadata header and scan footer."""
        ...

```