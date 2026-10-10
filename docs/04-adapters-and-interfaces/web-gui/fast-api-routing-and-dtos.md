# FastAPI routing & DTO specifications

## Overview

The web API layer (`lektor.adapters.gui.routers`) exposes endpoints grouped into functional routers. It maps incoming HTTP payloads to application command DTOs and serializes domain responses into Pydantic models.

---

## 1. Router registry

```text
lektor/adapters/gui/routers/
├── converter.py    # PDF splitting, vision translation, scans rendering, SSE telemetry
├── generator.py    # Single-page and batch audio speech synthesis, cancellation
├── player.py       # Audio streaming, range headers, playlist exploration
├── studio.py       # Ad-hoc snippet synthesis, recording history, WAV deletion
├── notes.py        # Reading notes auto-save and retrieval
├── books.py        # Book catalog, active switch, metadata updates
└── web.py          # Static asset routing and HTML templates

```

---

## 2. Data transfer objects (Pydantic models)

Defined in `lektor.adapters.gui.dtos`:

### `StartConversionRequest`

```python
class StartConversionRequest(BaseModel):
    book_slug: str
    pdf_path: Optional[str] = None
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    dpi: int = Field(default=300, ge=72, le=600)
    custom_prompt: Optional[str] = None
    skip_existing: bool = True

```

### `SynthesizePageRequest`

```python
class SynthesizePageRequest(BaseModel):
    page_id: str
    skip_existing: bool = False
    save_normalized_text: bool = True
    audio_format: Literal["wav", "mp3"] = "wav"

```

### `SynthesizeSnippetRequest`

```python
class SynthesizeSnippetRequest(BaseModel):
    markdown: str
    snippet_id: Optional[str] = None
    language_mode: Literal["bilingual", "pl", "en"] = "bilingual"
    force: bool = False

```

---

## 3. Partial content streaming (`/audio/{slug}/{track}`)

The player router handles byte-range HTTP requests (`Range: bytes=start-end`) returning status `206 Partial Content`. This architecture supports instantaneous audio scrubbing without transferring entire files.
