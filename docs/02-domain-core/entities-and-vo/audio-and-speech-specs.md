# Audio & speech specifications

## Overview

This document specifies the core domain structures, immutable value objects, and runtime configuration models governing audio signal representation, speech segmentation, and digital signal metrics.

---

## 1. Domain types and literal enumerations

Located in `lektor.domain.audio_models`, these literal types represent language modes, coding styles, and container formats:

```python
LanguageMode = Literal["bilingual", "pl", "en"]
CodeMode = Literal["spoken", "literal", "skip"]
AudioFormat = Literal["wav", "mp3", "flac"]

```

* **`LanguageMode`**: Controls linguistic normalization behavior. In `bilingual` mode, text is read in Polish while programming terms and code listings are pronounced with native English phonetics.
* **`CodeMode`**: Directs code verbalization: `spoken` verbalizes Go idioms naturally, `literal` reads exact syntax token by token, and `skip` strips code blocks.
* **`AudioFormat`**: Defines the physical container encoding for audio export.

---

## 2. Immutable value objects

### `AudioSpec`

Specifies physical acoustic sampling parameters:

```python
@dataclass(frozen=True)
class AudioSpec:
    sample_rate: int = 24000
    channels: int = 1
    sample_width: int = 2  # 16-bit PCM
    format: AudioFormat = "wav"

```

### `SpeechSegment`

Represents an indivisible linguistic utterance ready for neural vocoder synthesis:

```python
@dataclass(frozen=True)
class SpeechSegment:
    text: str
    lang: str = "pl"
    pause_after_ms: int = 300
    is_code: bool = False
    rate: float = 1.0

```

* **`text`**: Fully normalized, phonetically cleaned string.
* **`lang`**: Target accent identifier (`pl` or `en`).
* **`pause_after_ms`**: Silence duration to append after this segment (typically 300 ms for sentences, 650 ms for code blocks, 800 ms for headings).
* **`is_code`**: Flag marking whether the segment originates from source code.

---

## 3. Buffer abstractions and synthesis entities

### `AudioBuffer`

Encapsulates zero-allocation 32-bit floating point PCM audio arrays:

```python
class AudioBuffer:
    def __init__(self, data: np.ndarray) -> None:
        if data.dtype != np.float32:
            data = data.astype(np.float32)
        self._data = data

    @property
    def data(self) -> np.ndarray:
        return self._data

    @property
    def duration_sec(self) -> float:
        return len(self._data) / 24000.0

```

### `SynthesisResult` & `SynthesisStats`

Carries synthesis outcomes, duration metrics, and cache telemetry back to callers:

```python
@dataclass(frozen=True)
class SynthesisStats:
    total_segments: int
    cached_segments: int
    synthesized_segments: int
    duration_sec: float
    elapsed_sec: float
    realtime_factor: float

@dataclass(frozen=True)
class SynthesisResult:
    audio_path: Path
    stats: SynthesisStats
    skipped_existing: bool = False

```