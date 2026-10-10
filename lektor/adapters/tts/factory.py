"""Factory for creating configured TTS engine instances."""

from pathlib import Path
from typing import Optional

from ...application.ports.audio_ports import (
    AudioCacheProtocol,
    AudioCleanerProtocol,
    TTSEngineProtocol,
)
from ...domain.audio_models import SynthesisConfig
from .mock_engine import MockTTSEngine
from .universal_engine import UniversalTTSEngine, UniversalTTSEngineOptions


class TTSEngineFactory:
    """
    Factory creating the appropriate TTS engine adapter according to configuration.
    Creates UniversalTTSEngine as Single Source of Truth by default.
    """

    @staticmethod
    def create(
        engine_type: str = "universal",
        model_name_or_path: str = "k2-fsa/OmniVoice",
        reference_voice_path: Optional[Path] = None,
        config: Optional[SynthesisConfig] = None,
        sample_rate: int = 24000,
        fallback_synth: Optional[TTSEngineProtocol] = None,
        cleaner: Optional[AudioCleanerProtocol] = None,
        cache: Optional[AudioCacheProtocol] = None,
    ) -> TTSEngineProtocol:
        """Creates an instance implementing TTSEngineProtocol with dependency inversion (DIP)."""
        engine_type_lower = engine_type.lower()
        if engine_type_lower == "mock":
            return MockTTSEngine(sample_rate=sample_rate)
        else:
            target_model = model_name_or_path
            if engine_type_lower in ("chatterbox", "cb") and target_model == "k2-fsa/OmniVoice":
                target_model = "ResembleAI/chatterbox"

            return UniversalTTSEngine(
                UniversalTTSEngineOptions(
                    model_name_or_path=target_model,
                    reference_voice_path=reference_voice_path,
                    config=config,
                    sample_rate=sample_rate,
                    fallback_synth=fallback_synth,
                    cleaner=cleaner,
                    cache=cache,
                )
            )
