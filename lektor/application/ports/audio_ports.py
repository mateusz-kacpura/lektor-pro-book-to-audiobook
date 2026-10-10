"""
lektor.application.ports.audio_ports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Input/output ports for audio synthesis and processing (TTS, stitcher, cleaner, cache).
Strict typing without Any.
"""

from pathlib import Path
from typing import Optional, Protocol, Sequence

from ...domain.audio_models import AudioBuffer, SynthesisConfig


class TTSEngineProtocol(Protocol):
    """Abstract contract for speech synthesis engine (TTS)."""

    def load_model(self) -> None:
        """Loads model and weights into memory."""
        ...

    def unload_model(self) -> None:
        """Unloads model and releases VRAM allocations from the accelerator."""
        ...

    def synthesize_segment(self, text: str, lang: str = "pl") -> AudioBuffer:
        """Synthesizes a single text segment into an audio sample buffer (AudioBuffer float32)."""
        ...

    def is_loaded(self) -> bool:
        """Returns True if model is initialized and ready in memory."""
        ...


class AudioStitcherProtocol(Protocol):
    """Abstract contract for audio processing and file exporting."""

    def stitch_segments(
        self,
        audio_segments: Sequence[tuple[AudioBuffer | Sequence[float], int]],
    ) -> AudioBuffer:
        """Combines list of tuples (chunk_audio, pause_after_ms) into a continuous audio stream."""
        ...

    def normalize_volume(
        self,
        audio: AudioBuffer,
        target_peak: float = 0.95,
    ) -> AudioBuffer:
        """Normalizes sample buffer volume."""
        ...

    def create_silence(self, duration_ms: int) -> AudioBuffer:
        """Generates a silence buffer of the specified duration."""
        ...

    def save_audio(
        self,
        audio: AudioBuffer,
        output_path: Path,
        format: str = "wav",
    ) -> Path:
        """Saves audio buffer to file."""
        ...

    def get_duration_sec(self, audio: AudioBuffer | Sequence[float]) -> float:
        """Calculates audio duration in seconds."""
        ...

    def audio_exists(self, output_path: Path, min_bytes: int = 0) -> bool:
        """Checks whether audio file exists and meets minimum size requirements."""
        ...

    def get_file_size_kb(self, output_path: Path) -> float:
        """Returns audio file size in kilobytes."""
        ...

    def get_file_duration_sec(self, output_path: Path) -> float:
        """Returns audio file duration in seconds."""
        ...


class VoiceDiscoveryProtocol(Protocol):
    """Abstract contract for discovering available speaker voice samples."""

    def discover_voices(self) -> list[dict[str, str]]:
        """Returns list of available speaker voice sample files."""
        ...


class AudioCleanerProtocol(Protocol):
    """Abstract contract for audio cleaner removing artifacts and vocoder noise."""

    def clean_tail(self, audio: AudioBuffer, sample_rate: int = 24000) -> AudioBuffer:
        """Cleans audio of speech artifacts, vocoder hum, and background noise (VAD, filters, fade-out)."""
        ...


class AudioCacheProtocol(Protocol):
    """Abstract contract for caching generated audio segments."""

    def get(
        self,
        text: str,
        lang: str = "pl",
        voice: Optional[str] = None,
        config: Optional[SynthesisConfig] = None,
        temperature: float = 0.35,
        cfg_weight: float = 0.7,
    ) -> Optional[AudioBuffer]:
        """Retrieves cached audio array or None on cache miss."""
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
        """Stores generated audio in cache."""
        ...
