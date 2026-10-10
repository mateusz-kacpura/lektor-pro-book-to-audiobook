# Audio ports & protocols

## Overview

This document specifies the abstract port contracts for neural speech synthesis, digital signal processing (DSP), audio stitching, caching, and voice reference discovery. Defined in `lektor.application.ports.audio_ports`, these interfaces insulate use cases from external audio frameworks.

---

## 1. `TTSEngineProtocol`

Declares the contract required for neural text-to-speech synthesis engines:

```python
class TTSEngineProtocol(Protocol):
    def load_model(self) -> None:
        """Loads neural model weights and vocoders into execution memory."""
        ...

    def unload_model(self) -> None:
        """Unloads weights and clears allocated VRAM from GPU acceleration."""
        ...

    def synthesize_segment(self, text: str, lang: str = "pl") -> AudioBuffer:
        """Synthesizes a single normalized text segment into an AudioBuffer (float32)."""
        ...

    def is_loaded(self) -> bool:
        """Returns True if the engine is initialized and ready for inference."""
        ...

```

---

## 2. `AudioStitcherProtocol`

Coordinates audio segment concatenation, pauses, volume normalization, and export:

```python
class AudioStitcherProtocol(Protocol):
    def stitch_segments(
        self,
        audio_segments: Sequence[tuple[AudioBuffer | Sequence[float], int]],
    ) -> AudioBuffer:
        """Merges a list of (audio_chunk, pause_after_ms) tuples into a continuous stream."""
        ...

    def normalize_volume(
        self,
        audio: AudioBuffer,
        target_peak: float = 0.95,
    ) -> AudioBuffer:
        """Normalizes audio buffer amplitude to prevent digital clipping."""
        ...

    def create_silence(self, duration_ms: int) -> AudioBuffer:
        """Generates a zero-value PCM buffer of specified millisecond duration."""
        ...

    def save_audio(
        self,
        audio: AudioBuffer,
        output_path: Path,
        format: str = "wav",
    ) -> Path:
        """Persists the audio buffer to disk."""
        ...

    def get_duration_sec(self, audio: AudioBuffer | Sequence[float]) -> float:
        """Calculates duration in seconds based on sampling rate."""
        ...

    def audio_exists(self, output_path: Path, min_bytes: int = 0) -> bool:
        """Checks if a valid audio file exists on disk."""
        ...

    def get_file_size_kb(self, output_path: Path) -> float:
        """Returns file size in kilobytes."""
        ...

    def get_file_duration_sec(self, output_path: Path) -> float:
        """Returns duration of a stored audio file in seconds."""
        ...

```

---

## 3. `AudioCleanerProtocol`

Defines the contract for signal conditioning and artifact elimination:

```python
class AudioCleanerProtocol(Protocol):
    def clean_tail(self, audio: AudioBuffer, sample_rate: int = 24000) -> AudioBuffer:
        """Cleans speech artifacts, vocoder rumble, and background noise via VAD and DSP."""
        ...

```

---

## 4. `AudioCacheProtocol`

Specifies content-addressable storage for speech segments:

```python
class AudioCacheProtocol(Protocol):
    def get(
        self,
        text: str,
        lang: str = "pl",
        voice: Optional[str] = None,
        config: Optional[SynthesisConfig] = None,
        temperature: float = 0.35,
        cfg_weight: float = 0.7,
    ) -> Optional[AudioBuffer]:
        """Retrieves cached audio buffer or returns None on cache miss."""
        ...

    def put(
        self,
        text: str,
        audio: AudioBuffer,
        lang: str = "pl",
        voice: Optional[str] = None,
        config: Optional[SynthesisConfig] = None,
        temperature: float = 0.35,
        cfg_weight: float = 0.7,
        sample_rate: int = 24000,
    ) -> None:
        """Stores synthesized audio in cache."""
        ...

```

---

## 5. `VoiceDiscoveryProtocol`

Provides discovery of narrator voice samples without hardcoded filesystem paths:

```python
class VoiceDiscoveryProtocol(Protocol):
    def discover_voices(self) -> list[dict[str, str]]:
        """Returns a list of available reference voice profiles and sample paths."""
        ...

```
