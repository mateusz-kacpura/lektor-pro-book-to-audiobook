"""Chatterbox multilingual TTS backend adapter."""

from pathlib import Path
from typing import Optional

import numpy as np
import torch

from ....domain.languages import provider_language_code
from .base import ModelBackendProtocol, to_numpy_float32


class ChatterboxBackend(ModelBackendProtocol):
    """Backend executing Chatterbox model inference."""

    def __init__(self) -> None:
        self._model: Optional[object] = None
        self._sample_rate: int = 24000

    def load(self, model_target: str, device: str) -> bool:
        try:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS

            print(f"[UniversalTTS/Chatterbox] Ładowanie modelu {model_target} na urządzeniu {device}...")
            model_path = Path(model_target)
            if model_path.exists() and model_path.is_dir():
                loaded = ChatterboxMultilingualTTS.from_local(model_path, device)
            else:
                loaded = ChatterboxMultilingualTTS.from_pretrained(device)

            self._model = loaded
            sr_val = getattr(loaded, "sr", 24000)
            self._sample_rate = int(sr_val)
            print(f"[UniversalTTS/Chatterbox] Model załadowany pomyślnie! (SR: {self._sample_rate} Hz)")
            return True
        except Exception as e:
            print(f"[UniversalTTS/Chatterbox] Błąd inicjalizacji: {e}")
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
        _ = speed
        if self._model is None:
            return np.zeros(0, dtype=np.float32)

        generate_fn = getattr(self._model, "generate", None)
        if not callable(generate_fn):
            return np.zeros(0, dtype=np.float32)

        conds = getattr(self._model, "conds", None)
        ref_path = reference_audio_path if conds is None else None

        wav = generate_fn(
            text=text,
            language_id=provider_language_code(lang or "pl", "chatterbox"),
            audio_prompt_path=ref_path,
            temperature=temperature,
            cfg_weight=cfg_weight,
            exaggeration=exaggeration,
            repetition_penalty=repetition_penalty,
        )
        return to_numpy_float32(wav)

    def get_sample_rate(self) -> int:
        return self._sample_rate

    def unload(self) -> None:
        self._model = None
        if torch is not None and torch.cuda.is_available():
            import gc
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        print("[UniversalTTS/Chatterbox] Model wyładowany, pamięć VRAM zwolniona.")
