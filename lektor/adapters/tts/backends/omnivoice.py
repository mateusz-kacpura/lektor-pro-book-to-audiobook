"""OmniVoice multilingual TTS backend adapter."""

from typing import Optional

import numpy as np
import torch

from ....domain.languages import provider_language_code
from .base import ModelBackendProtocol, to_numpy_float32


class OmniVoiceBackend(ModelBackendProtocol):
    """Backend executing OmniVoice model inference."""

    def __init__(self) -> None:
        self._model: Optional[object] = None
        self._sample_rate: int = 24000

    def load(self, model_target: str, device: str) -> bool:
        try:
            from omnivoice import OmniVoice

            dtype_val = None
            if torch is not None:
                dtype_val = torch.float16 if "cuda" in device else torch.float32

            print(f"[UniversalTTS/OmniVoice] Ładowanie modelu {model_target} na urządzeniu {device}...")
            loaded = OmniVoice.from_pretrained(
                model_target,
                device_map=device,
                dtype=dtype_val,
            )
            self._model = loaded
            sr_val = getattr(loaded, "sampling_rate", None)
            if sr_val:
                self._sample_rate = int(sr_val)
            print(f"[UniversalTTS/OmniVoice] Model załadowany pomyślnie! (SR: {self._sample_rate} Hz)")
            return True
        except Exception as e:
            print(f"[UniversalTTS/OmniVoice] Błąd inicjalizacji: {e}")
            return False

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
        _ = (temperature, cfg_weight, exaggeration, repetition_penalty)
        if self._model is None:
            return np.zeros(0, dtype=np.float32)

        generate_fn = getattr(self._model, "generate", None)
        if not callable(generate_fn):
            return np.zeros(0, dtype=np.float32)

        results = generate_fn(
            text=text,
            language=provider_language_code(lang or "pl", "omnivoice"),
            ref_audio=reference_audio_path,
            speed=speed,
        )
        if not results or len(results) == 0:
            return np.zeros(0, dtype=np.float32)

        return to_numpy_float32(results[0])

    def get_sample_rate(self) -> int:
        return self._sample_rate

    def unload(self) -> None:
        self._model = None
        if torch is not None and torch.cuda.is_available():
            import gc
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        print("[UniversalTTS/OmniVoice] Model wyładowany, pamięć VRAM zwolniona.")
