"""Abstract base interface for model execution backends."""

from typing import Optional, Protocol

import numpy as np


class ModelBackendProtocol(Protocol):
    """Protocol defining model execution lifecycle."""

    def load(self, model_target: str, device: str) -> bool:
        """Loads weights and initializes model."""
        ...

    def generate(
        self,
        text: str,
        lang: str,
        reference_audio_path: Optional[str],
        speed: float,
        temperature: float,
        cfg_weight: float,
        exaggeration: float,
        repetition_penalty: float,
    ) -> np.ndarray:
        """Generates audio signal as NumPy float32 array."""
        ...

    def get_sample_rate(self) -> int:
        """Returns model sampling rate in Hz."""
        ...

    def unload(self) -> None:
        """Unloads model instance and clears VRAM memory."""
        ...


def to_numpy_float32(data: object) -> np.ndarray:
    """Safe conversion of PyTorch tensor or array to 1D NumPy float32."""
    if isinstance(data, np.ndarray):
        return data.squeeze().astype(np.float32)

    if hasattr(data, "detach"):
        detached = getattr(data, "detach")()
        cpu_tensor = getattr(detached, "cpu")()
        numpy_arr = getattr(cpu_tensor, "numpy")()
        return np.asarray(numpy_arr, dtype=np.float32).squeeze()

    return np.asarray(data, dtype=np.float32).squeeze()
