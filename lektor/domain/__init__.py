"""Domain Layer (Entities Layer)."""

from .audio_models import (
    AudioFormat,
    AudioSpec,
    CodeMode,
    LanguageMode,
    PageNumber,
    SpeechSegment,
    SynthesisConfig,
    SynthesisResult,
    SynthesisStats,
)
from .book_models import (
    Book,
    BookMetadata,
    BookPageMetadata,
    BookPaths,
    DataPaths,
)
from .normalization import TextNormalizationService
from .ocr_models import OCRBlockResult, OCRPageResult
from .resource_models import (
    SLOT_AUDIO_TTS,
    SLOT_VISION,
    ModelLeaseState,
    ModelResourceId,
    ModelSlotId,
    VramSnapshot,
)
from .studio_models import StudioItem

__all__ = [
    "AudioFormat",
    "AudioSpec",
    "Book",
    "BookMetadata",
    "BookPageMetadata",
    "BookPaths",
    "CodeMode",
    "DataPaths",
    "LanguageMode",
    "ModelLeaseState",
    "ModelResourceId",
    "ModelSlotId",
    "OCRBlockResult",
    "OCRPageResult",
    "PageNumber",
    "SLOT_AUDIO_TTS",
    "SLOT_VISION",
    "SpeechSegment",
    "StudioItem",
    "SynthesisConfig",
    "SynthesisResult",
    "SynthesisStats",
    "TextNormalizationService",
    "VramSnapshot",
]