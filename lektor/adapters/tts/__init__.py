"""Text-to-Speech synthesis adapters."""

from .base import BaseSynthesizer
from .cache import AudioSegmentCache
from .factory import TTSEngineFactory
from .mock_engine import MockTTSEngine
from .universal_engine import (
    ChatterboxSynthesizer,
    ChatterboxTTSEngine,
    OmniVoiceSynthesizer,
    OmniVoiceTTSEngine,
    UniversalSynthesizerAdapter,
    UniversalTTSEngine,
    UniversalTTSEngineOptions,
)

__all__ = [
    "BaseSynthesizer",
    "AudioSegmentCache",
    "UniversalTTSEngine",
    "UniversalTTSEngineOptions",
    "UniversalSynthesizerAdapter",
    "OmniVoiceSynthesizer",
    "OmniVoiceTTSEngine",
    "ChatterboxSynthesizer",
    "ChatterboxTTSEngine",
    "MockTTSEngine",
    "TTSEngineFactory",
]
