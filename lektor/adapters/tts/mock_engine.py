"""Mock TTS engine adapter for fast unit testing and offline development."""

import numpy as np

from ...application.ports.audio_ports import TTSEngineProtocol
from ...domain.audio_models import AudioBuffer, make_audio_buffer


class MockTTSEngine(TTSEngineProtocol):
    """Mock TTS engine generating synthetic sine wave tones."""

    def __init__(self, sample_rate: int = 24000) -> None:
        self.sample_rate = sample_rate
        self._loaded: bool = False
        self.synthesized_calls: list[tuple[str, str]] = []

    def load_model(self) -> None:
        """Loads model and weights into memory."""
        self._loaded = True

    def unload_model(self) -> None:
        """Unloads model and releases VRAM memory from the accelerator."""
        self._loaded = False

    def is_loaded(self) -> bool:
        """Returns True if model is loaded and ready."""
        return self._loaded

    def synthesize_segment(self, text: str, lang: str = "pl") -> AudioBuffer:
        """Synthesizes single text segment into AudioBuffer float32."""
        self.synthesized_calls.append((text, lang))
        duration_samples = max(len(text) * 80, int(self.sample_rate * 0.1))
        return make_audio_buffer(np.zeros(duration_samples, dtype=np.float32))
