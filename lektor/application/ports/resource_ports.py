"""
lektor.application.ports.resource_ports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Input/output ports for AI model lifecycle management and GPU VRAM arbitration.
Strict typing without Any.
"""

from typing import Optional, Protocol

from ...domain.resource_models import (
    ModelResourceId,
    ModelSlotId,
    VramSnapshot,
)


class AIModelHandleProtocol(Protocol):
    """
    Abstract contract for an individual AI model handle.
    Allows dynamic loading, unloading, and state monitoring.
    """

    @property
    def slot_id(self) -> ModelSlotId:
        """Logical slot identifier (e.g. SLOT_VISION, SLOT_AUDIO_TTS)."""
        ...

    @property
    def resource_id(self) -> ModelResourceId:
        """Resource/model identifier (e.g. google/gemma-4-12b, k2-fsa/OmniVoice)."""
        ...

    def load(self) -> None:
        """Loads model into accelerator memory (GPU) or starts server process."""
        ...

    def unload(self) -> None:
        """Releases VRAM memory (terminates server process or clears PyTorch cache)."""
        ...

    def is_loaded(self) -> bool:
        """Returns True if model is active in memory and ready for inference."""
        ...


class AIModelArbiterProtocol(Protocol):
    """
    Abstract contract for the central GPU / VRAM resource arbiter.
    Manages mutual exclusion of models on the GPU (Mutual Exclusion / Preemption).
    """

    def acquire(self, slot_id: ModelSlotId) -> None:
        """
        Leases accelerator resource for the specified slot.
        Automatically unloads existing model and clears VRAM if another model occupies GPU.
        """
        ...

    def release(self, slot_id: ModelSlotId) -> None:
        """Releases resource for the specified slot and clears GPU memory."""
        ...

    def release_all(self) -> None:
        """Releases all models and restores clean GPU memory state."""
        ...

    def get_active_slot(self) -> Optional[ModelSlotId]:
        """Returns currently active model slot or None."""
        ...

    def get_vram_snapshot(self) -> VramSnapshot:
        """Retrieves current VRAM memory telemetry snapshot."""
        ...
