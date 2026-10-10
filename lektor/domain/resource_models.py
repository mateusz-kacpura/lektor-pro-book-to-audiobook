"""
lektor.domain.resource_models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Domain models for GPU computing resource and VRAM allocation management.
Entities Layer (Domain Layer).
Zero dependencies on frameworks or operating systems.
Strict typing without Any.
"""

from dataclasses import dataclass
from enum import Enum
from typing import NewType

ModelSlotId = NewType("ModelSlotId", str)
ModelResourceId = NewType("ModelResourceId", str)

SLOT_VISION = ModelSlotId("vision_ocr")
SLOT_AUDIO_TTS = ModelSlotId("audio_tts")


class ModelLeaseState(str, Enum):
    """State of GPU compute lease for a specific model."""
    IDLE = "IDLE"
    ACQUIRING = "ACQUIRING"
    ACTIVE = "ACTIVE"
    RELEASING = "RELEASING"


@dataclass(frozen=True)
class VramSnapshot:
    """Immutable telemetry snapshot of GPU VRAM memory."""
    used_mb: float
    total_mb: float
    free_mb: float

    @property
    def utilization_pct(self) -> float:
        """Returns percentage utilization of GPU VRAM."""
        if self.total_mb <= 0:
            return 0.0
        return min(100.0, max(0.0, (self.used_mb / self.total_mb) * 100.0))


__all__ = [
    "ModelSlotId",
    "ModelResourceId",
    "ModelLeaseState",
    "VramSnapshot",
    "SLOT_VISION",
    "SLOT_AUDIO_TTS",
]
