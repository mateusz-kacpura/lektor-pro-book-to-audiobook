"""
lektor.application.ports
~~~~~~~~~~~~~~~~~~~~~~~~
Input and output port definitions (DIP).
"""

from .audio_ports import (
    AudioCacheProtocol,
    AudioCleanerProtocol,
    AudioStitcherProtocol,
    TTSEngineProtocol,
)
from .ocr_ports import (
    BookMarkdownFormatterProtocol,
    PdfSplitterProtocol,
    VisionApiClientProtocol,
    VisionApiResponse,
    VisionPromptBuilderProtocol,
    VisionTranslatorProtocol,
)
from .resource_ports import (
    AIModelArbiterProtocol,
    AIModelHandleProtocol,
)
from .storage_ports import (
    BookReaderProtocol,
    BookRepositoryProtocol,
    BookWriterProtocol,
    NotesRepositoryProtocol,
    PageRepositoryProtocol,
    StudioHistoryRepositoryProtocol,
)
from .telemetry_ports import (
    GpuTelemetryProtocol,
    ProgressReporterProtocol,
    TelemetryBroadcasterProtocol,
)

__all__ = [
    "AIModelArbiterProtocol",
    "AIModelHandleProtocol",
    "AudioCacheProtocol",
    "AudioCleanerProtocol",
    "AudioStitcherProtocol",
    "BookMarkdownFormatterProtocol",
    "BookReaderProtocol",
    "BookRepositoryProtocol",
    "BookWriterProtocol",
    "GpuTelemetryProtocol",
    "NotesRepositoryProtocol",
    "PageRepositoryProtocol",
    "PdfSplitterProtocol",
    "ProgressReporterProtocol",
    "StudioHistoryRepositoryProtocol",
    "TTSEngineProtocol",
    "TelemetryBroadcasterProtocol",
    "VisionApiClientProtocol",
    "VisionApiResponse",
    "VisionPromptBuilderProtocol",
    "VisionTranslatorProtocol",
]