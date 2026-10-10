"""
lektor.domain.audio_models
~~~~~~~~~~~~~~~~~~~~~~~~~
Entities and Value Objects for audio processing and speech synthesis.
Strict typing without Any (Python 3.14+).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence, cast

from .book_models import PageNumber as PageNumber

# Implementation note: see the surrounding code for the behavior described here.
AudioBuffer = Sequence[float]

def make_audio_buffer(data: object) -> AudioBuffer:
    """Applies domain contract to audio buffer without external audio library dependencies."""
    return cast(AudioBuffer, data)

CodeMode = Literal["spoken", "summary", "skip"]
LanguageMode = str
AudioFormat = Literal["wav", "mp3"]


@dataclass(frozen=True)
class SpeechSegment:
    """Entity representing an elementary fragment of synthesized speech with text and pauses."""
    text: str
    lang: str                  # 'pl' or 'en'
    pause_after_ms: int = 350  # DĹ‚ugoĹ›Ä‡ pauzy po segmencie w ms
    is_header: bool = False
    is_code: bool = False

    def __post_init__(self) -> None:
        if not self.lang:
            object.__setattr__(self, "lang", "pl")
        if self.pause_after_ms < 0:
            object.__setattr__(self, "pause_after_ms", 0)


@dataclass(frozen=True)
class AudioSpec:
    """Immutable Value Object describing technical parameters of an audio stream."""
    sample_rate: int = 24000
    audio_format: AudioFormat = "wav"
    target_peak: float = 0.95

    def __post_init__(self) -> None:
        if self.sample_rate <= 0:
            raise ValueError(f"Niepoprawny sample_rate: {self.sample_rate}")
        if not (0.0 < self.target_peak <= 1.0):
            raise ValueError(f"target_peak musi byÄ‡ w przedziale (0, 1], otrzymano: {self.target_peak}")


@dataclass(frozen=True)
class SynthesisConfig:
    """
    Value Object z parametrami syntezy mowy TTS.
    """
    temperature: float = 0.35
    cfg_weight: float = 0.7
    exaggeration: float = 0.25
    repetition_penalty: float = 1.8
    trim_trailing_silence: bool = True
    device: str = "auto"
    reference_voice_path: Path | None = None


@dataclass(frozen=True)
class SynthesisStats:
    """Value Object representing synthesis performance and execution speed statistics."""
    char_count: int
    word_count: int
    segment_count: int
    duration_sec: float
    audio_duration_sec: float

    @property
    def rtf(self) -> float:
        """Real-Time Factor (RTF)."""
        if self.audio_duration_sec > 0:
            return self.duration_sec / self.audio_duration_sec
        return 0.0

    @property
    def speed_factor(self) -> float:
        """Returns synthesis speed factor relative to real-time (e.g. 2.5x)."""
        if self.duration_sec > 0 and self.audio_duration_sec > 0:
            return self.audio_duration_sec / self.duration_sec
        return 0.0

    @property
    def chars_per_sec(self) -> float:
        """Synthesis throughput in characters per second."""
        if self.duration_sec > 0:
            return self.char_count / self.duration_sec
        return 0.0


@dataclass(frozen=True)
class SynthesisResult:
    """
    Wynik procesu syntezy pojedynczej strony.
    """
    audio_path: Path
    segments: Sequence[SpeechSegment]
    stats: SynthesisStats
    skipped_existing: bool = False
