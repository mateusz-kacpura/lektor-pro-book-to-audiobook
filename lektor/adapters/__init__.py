"""Interface Adapters Layer."""

from .audio import NumpyAudioStitcher
from .cli import main as cli_main
from .ocr import (
    DefaultBookMarkdownFormatter,
    DefaultVisionPromptBuilder,
    GemmaVisionTranslatorAdapter,
    OpenAiVisionHttpClient,
    PyMuPdfSplitterAdapter,
    QwenVisionTranslatorAdapter,
    UniversalVisionTranslatorAdapter,
    VisionTranslatorAdapter,
)
from .resources import (
    DynamicVramModelArbiter,
    ProcessModelHandle,
    PyTorchModelHandle,
)
from .storage import FileSystemPageRepository
from .tts import (
    ChatterboxTTSEngine,
    MockTTSEngine,
    OmniVoiceTTSEngine,
    TTSEngineFactory,
    UniversalTTSEngine,
)

__all__ = [
    "DynamicVramModelArbiter",
    "ProcessModelHandle",
    "PyTorchModelHandle",
    "UniversalTTSEngine",
    "OmniVoiceTTSEngine",
    "ChatterboxTTSEngine",
    "DefaultBookMarkdownFormatter",
    "DefaultVisionPromptBuilder",
    "FileSystemPageRepository",
    "GemmaVisionTranslatorAdapter",
    "MockTTSEngine",
    "NumpyAudioStitcher",
    "OpenAiVisionHttpClient",
    "PyMuPdfSplitterAdapter",
    "QwenVisionTranslatorAdapter",
    "TTSEngineFactory",
    "UniversalVisionTranslatorAdapter",
    "VisionTranslatorAdapter",
    "cli_main",
]
