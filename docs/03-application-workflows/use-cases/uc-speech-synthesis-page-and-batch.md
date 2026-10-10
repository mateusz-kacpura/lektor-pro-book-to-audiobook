# Use case: speech synthesis (page and batch)

## Overview

These interactors orchestrate neural speech generation from Markdown pages. Managed by `SynthesizePageUseCase` (`lektor.application.use_cases.synthesize_page`) and `BatchSynthesisUseCase` (`lektor.application.use_cases.batch_synthesis`), they convert text structures into concatenated, normalized audio tracks.

---

## 1. Page synthesis execution pipeline

```mermaid
sequenceDiagram
    autonumber
    participant Caller as CLI / GUI Worker
    participant UC as SynthesizePageUseCase
    participant Arbiter as AIModelArbiterProtocol
    participant Repo as PageRepositoryProtocol
    participant Norm as TextNormalizationService
    participant TTS as TTSEngineProtocol
    participant Stitcher as AudioStitcherProtocol

    Caller->>UC: execute(SynthesizePageCommand)
    activate UC
    
    opt Model Arbiter Present
        UC->>Arbiter: acquire(SLOT_AUDIO_TTS)
    end
    
    UC->>Repo: audio_exists(out_path)?
    alt Skip existing is True and audio exists
        UC-->>Caller: SynthesisResult(skipped_existing=True)
    end

    UC->>Repo: read_markdown(markdown_path)
    UC->>Norm: normalize(raw_markdown)
    activate Norm
    Norm-->>UC: list[SpeechSegment]
    deactivate Norm

    UC->>Repo: save_preview(page_normalized.txt)

    loop For each segment in page
        UC->>TTS: synthesize_segment(seg.text, seg.lang)
        activate TTS
        TTS-->>UC: chunk (AudioBuffer)
        deactivate TTS
    end

    UC->>Stitcher: stitch_segments(chunks, pauses)
    UC->>Stitcher: save_audio(stitched_audio, out_path)
    UC->>Repo: save_state(page_state.json, stats)

    UC-->>Caller: SynthesisResult(audio_path, stats)
    deactivate UC

```

---

## 2. Inbound and outbound contracts

### Commands

```python
@dataclass(frozen=True)
class SynthesizePageCommand:
    markdown_path: Path
    output_dir: Path
    skip_existing: bool = False
    save_normalized_text: bool = True
    audio_format: str = "wav"

@dataclass(frozen=True)
class BatchSynthesisCommand:
    pages_dir: Path
    output_dir: Path
    pattern: str = "page_*.md"
    skip_existing: bool = True
    save_normalized_text: bool = True
    audio_format: str = "wav"

```

---

## 3. Batch coordination and cooperative cancellation

`BatchSynthesisUseCase` iterates through discovered Markdown files sorted numerically. Before processing each page, it queries `progress_reporter.check_cancellation()`. If signaled, it breaks out of the loop cleanly, permitting callers to halt generation without corrupting the file system.
