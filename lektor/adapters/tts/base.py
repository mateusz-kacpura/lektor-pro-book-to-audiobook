"""Base classes and protocols for TTS engine adapters."""

from abc import ABC, abstractmethod

from ...application.ports.audio_ports import TTSEngineProtocol
from ...domain.audio_models import AudioBuffer


class BaseSynthesizer(ABC, TTSEngineProtocol):
    """Abstract base adapter for speech synthesis engines."""

    def __init__(self, sample_rate: int = 24000) -> None:
        self.sample_rate = sample_rate
        self._loaded: bool = False

    def is_loaded(self) -> bool:
        return self._loaded

    @abstractmethod
    def load_model(self) -> None:
        """Loads model and weights into memory."""
        pass

    @abstractmethod
    def unload_model(self) -> None:
        """Unloads model and releases VRAM memory from the accelerator."""
        pass

    @abstractmethod
    def synthesize_segment(self, text: str, lang: str = "pl") -> AudioBuffer:
        """Synthesizes single text segment into AudioBuffer float32."""
        pass
