# Use case: vision AI translation

## Overview

The `ConvertPdfBookUseCase` (`lektor.application.use_cases.convert_pdf_book`) coordinates the multimodal pipeline: document page splitting, image verification, vision model inference, code protection, and real-time telemetry emission.

---

## 1. End-to-end execution pipeline

```mermaid
sequenceDiagram
    autonumber
    participant Worker as Background Task
    participant UC as ConvertPdfBookUseCase
    participant Arbiter as AIModelArbiterProtocol
    participant Splitter as PdfSplitterProtocol
    participant Vision as VisionTranslatorProtocol
    participant Validator as MarkdownPageValidationService
    participant Repo as PageRepositoryProtocol
    participant Sse as TelemetryBroadcasterProtocol

    Worker->>UC: execute(StartConversionCommand, job)
    activate UC
    
    UC->>Arbiter: acquire(SLOT_VISION)
    
    alt Existing scans already present on disk
        UC->>UC: Reuse existing JPEG bitmaps (Bypass rendering)
    else Missing scans detected
        UC->>Splitter: split_pdf(dpi=300)
    end

    loop For each page in document
        alt Cancellation signaled
            UC->>Sse: broadcast(CANCELLED)
            break
        end

        UC->>Sse: broadcast(TRANSLATING, current_page, step_desc)
        
        alt Page Markdown already exists and skip_existing=True
            UC->>UC: job.mark_page_completed()
        else Run multimodal extraction
            try
                UC->>Vision: translate_scan(scan, custom_prompt)
                activate Vision
                Vision-->>UC: TranslatedMarkdownPage
                deactivate Vision
                UC->>Validator: validate_page_integrity(markdown)
                UC->>Repo: write_markdown(out_page_path, markdown)
                UC->>UC: job.mark_page_completed()
            catch Exception
                UC->>UC: job.mark_page_failed(page_num, error_str)
                UC->>Sse: broadcast(ERROR, error_str)
            end
        end

        UC->>Sse: broadcast(telemetry snapshot with tokens_per_sec, eta, vram)
    end

    UC->>Sse: broadcast(COMPLETED)
    deactivate UC

```

---

## 2. Inbound command contract

```python
@dataclass(frozen=True)
class StartConversionCommand:
    pdf_path: Path
    book_slug: BookSlug
    dpi: int = 300
    custom_prompt: Optional[str] = None
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    skip_existing: bool = True
    scans_dir: Optional[Path] = None
    pages_dir: Optional[Path] = None

```

---

## 3. Invariants and operational resilience

* **Scan reuse**: If valid 300 DPI scans exist in `scans/`, PDF rendering is bypassed, transitioning directly to inference.
* **Fault tolerance (`BR-013`)**: Errors on page $K$ are logged to `job.failed_pages` without terminating the loop; processing advances to page $K+1$.
* **Telemetry accuracy (`BR-014`)**: Every iteration queries `GpuTelemetryProtocol` and computes real-time tokens per second and ETA.
