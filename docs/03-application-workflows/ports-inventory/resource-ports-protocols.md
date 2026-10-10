# Resource ports & protocols

## Overview

This specification details contracts for computational resource arbitration and lifecycle control of artificial intelligence models. Defined in `lektor.application.ports.resource_ports`, these interfaces enable mutual exclusion on graphics hardware without exposing hardware drivers to application use cases.

---

## 1. `AIModelHandleProtocol`

Defines the contract for an individual model lifecycle handle:

```python
class AIModelHandleProtocol(Protocol):
    @property
    def slot_id(self) -> ModelSlotId:
        """Logical slot identifier (e.g. SLOT_VISION, SLOT_AUDIO_TTS)."""
        ...

    @property
    def resource_id(self) -> ModelResourceId:
        """Model resource identifier (e.g. google/gemma-4-12b, k2-fsa/OmniVoice)."""
        ...

    def load(self) -> None:
        """Loads model weights into accelerator VRAM or spawns local inference process."""
        ...

    def unload(self) -> None:
        """Releases VRAM by terminating processes or flushing PyTorch CUDA allocations."""
        ...

    def is_loaded(self) -> bool:
        """Returns True if the model is initialized in memory and ready for requests."""
        ...

```

---

## 2. `AIModelArbiterProtocol`

Governs hardware mutual exclusion and model preemption across the single GPU:

```python
class AIModelArbiterProtocol(Protocol):
    def acquire(self, slot_id: ModelSlotId) -> None:
        """
        Leases GPU hardware for the requested slot.
        If another model occupies memory, unloads it and flushes VRAM first.
        """
        ...

    def release(self, slot_id: ModelSlotId) -> None:
        """Releases the slot resource and clears accelerator allocations."""
        ...

    def release_all(self) -> None:
        """Evicts all registered model handles and restores clean GPU state."""
        ...

    def get_active_slot(self) -> Optional[ModelSlotId]:
        """Returns currently leased slot identifier, or None if idle."""
        ...

    def get_vram_snapshot(self) -> VramSnapshot:
        """Queries hardware driver for real-time used, total, and free VRAM megabytes."""
        ...

```