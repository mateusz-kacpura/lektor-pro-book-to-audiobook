# Przypadek użycia: synteza mowy (pojedyncza strona i przetwarzanie wsadowe)

## Przegląd

Interaktory tej grupy koordynują proces zamiany tekstu Markdown na mowę syntetyczną. Realizowane przez `SynthesizePageUseCase` (`lektor.application.use_cases.synthesize_page`) oraz `BatchSynthesisUseCase` (`lektor.application.use_cases.batch_synthesis`), przekształcają one dokumenty tekstowe w połączone i znormalizowane pliki dźwiękowe.

---

## 1. Potok wykonawczy syntezy pojedynczej strony

```mermaid
sequenceDiagram
    autonumber
    participant Caller as Wątek roboczy CLI / GUI
    participant UC as SynthesizePageUseCase
    participant Arbiter as AIModelArbiterProtocol
    participant Repo as PageRepositoryProtocol
    participant Norm as TextNormalizationService
    participant TTS as TTSEngineProtocol
    participant Stitcher as AudioStitcherProtocol

    Caller->>UC: execute(SynthesizePageCommand)
    activate UC
    
    opt Obecny arbiter VRAM
        UC->>Arbiter: acquire(SLOT_AUDIO_TTS)
    end
    
    UC->>Repo: audio_exists(out_path)?
    alt Pomijanie włączone i plik audio istnieje
        UC-->>Caller: SynthesisResult(skipped_existing=True)
    end

    UC->>Repo: read_markdown(markdown_path)
    UC->>Norm: normalize(raw_markdown)
    activate Norm
    Norm-->>UC: list[SpeechSegment]
    deactivate Norm

    UC->>Repo: save_preview(page_normalized.txt)

    loop Dla każdego segmentu wypowiedzi
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

## 2. Kontrakty danych wejściowych i wyjściowych

### Komendy

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

## 3. Orkiestracja wsadowa i kooperacyjne zatrzymywanie

`BatchSynthesisUseCase` odnajduje pliki stron posortowane numerycznie. Przed rozpoczęciem każdej strony odpytuje metodę `progress_reporter.check_cancellation()`. W przypadku wykrycia sygnału zatrzymania pętla przerywa pracę, co pozwala na bezpieczne zatrzymanie zadania bez uszkadzania stanu plików.
