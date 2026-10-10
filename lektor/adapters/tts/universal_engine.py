"""Universal TTS engine adapter delegating to modular backends (Chatterbox / OmniVoice)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from ...application.ports.audio_ports import (
    AudioCacheProtocol,
    AudioCleanerProtocol,
    TTSEngineProtocol,
)
from ...domain.audio_models import AudioBuffer, SynthesisConfig, make_audio_buffer
from ..audio.cleaner import SileroAudioCleaner

# ============================================================================
# Model execution backends (DIP / OCP / Modular Backends)
# ============================================================================
from .backends import (
    ChatterboxBackend,
    ModelBackendProtocol,
    OmniVoiceBackend,
    to_numpy_float32,
)
from .base import BaseSynthesizer

# Implementation note: see the surrounding code for the behavior described here.
_OmniVoiceBackend = OmniVoiceBackend
_ChatterboxBackend = ChatterboxBackend
_to_numpy_float32 = to_numpy_float32


class _NullAudioCache(AudioCacheProtocol):
    """No-op audio cache used when no cache adapter is injected."""

    def get(
        self,
        text: str,
        lang: str = "pl",
        voice: Optional[str] = None,
        config: Optional[SynthesisConfig] = None,
        temperature: float = 0.35,
        cfg_weight: float = 0.7,
    ) -> Optional[AudioBuffer]:
        _ = (text, lang, voice, config, temperature, cfg_weight)
        return None

    def put(
        self,
        text: str,
        audio: AudioBuffer,
        lang: str = "pl",
        voice: Optional[str] = None,
        config: Optional[SynthesisConfig] = None,
        temperature: float = 0.35,
        cfg_weight: float = 0.7,
        sample_rate: int = 24000,
    ) -> None:
        _ = (text, audio, lang, voice, config, temperature, cfg_weight, sample_rate)


@dataclass(frozen=True)
class UniversalTTSEngineOptions:
    """Skupia konfiguracje i zaleznosci wymagane przez uniwersalny silnik TTS."""

    model_name_or_path: Optional[str] = None
    reference_voice_path: Path | str | None = None
    device: Optional[str] = None
    sample_rate: int = 24000
    speed: float = 1.0
    temperature: float = 0.35
    cfg_weight: float = 0.7
    exaggeration: float = 0.25
    repetition_penalty: float = 1.8
    trim_trailing_silence: bool = True
    cache: Optional[AudioCacheProtocol] = None
    fallback_synth: Optional[TTSEngineProtocol] = None
    cleaner: Optional[AudioCleanerProtocol] = None
    config: Optional[SynthesisConfig] = None


class UniversalTTSEngine(BaseSynthesizer):
    """Engine adapter implementing TTSEngineProtocol."""

    def __init__(self, options: Optional[UniversalTTSEngineOptions] = None) -> None:
        settings = options or UniversalTTSEngineOptions()
        super().__init__(sample_rate=settings.sample_rate)

        config = settings.config
        resolved_model = (
            settings.model_name_or_path
            or os.environ.get("LEKTOR_TTS_MODEL")
            or os.environ.get("LEKTOR_OMNIVOICE_MODEL")
            or "k2-fsa/OmniVoice"
        )
        self.model_name_or_path: str = resolved_model
        self.reference_voice_path: Optional[Path | str] = settings.reference_voice_path or (
            config.reference_voice_path if config else None
        )
        self.speed: float = settings.speed
        self.temperature: float = config.temperature if config else settings.temperature
        self.cfg_weight: float = config.cfg_weight if config else settings.cfg_weight
        self.exaggeration: float = config.exaggeration if config else settings.exaggeration
        self.repetition_penalty: float = config.repetition_penalty if config else settings.repetition_penalty
        self.trim_trailing_silence: bool = config.trim_trailing_silence if config else settings.trim_trailing_silence

        target_device = config.device if (config and config.device != "auto") else settings.device
        if target_device:
            self.device = target_device
        elif torch is not None and torch.cuda.is_available():
            self.device = "cuda:0"
        else:
            self.device = "cpu"

        self.fallback_synth: Optional[TTSEngineProtocol] = settings.fallback_synth
        self.cache: AudioCacheProtocol = settings.cache if settings.cache is not None else _NullAudioCache()
        self.cleaner: AudioCleanerProtocol = (
            settings.cleaner if settings.cleaner is not None else SileroAudioCleaner(sample_rate=settings.sample_rate)
        )
        self._backend: Optional[ModelBackendProtocol] = None

    def _select_backend(self) -> ModelBackendProtocol:
        """Dynamicznie dobiera odpowiedni backend na podstawie identyfikatora modelu."""
        model_str = self.model_name_or_path.lower()
        if "chatterbox" in model_str:
            return _ChatterboxBackend()
        # Implementation note: see the surrounding code for the behavior described here.
        return _OmniVoiceBackend()

    def load_model(self) -> None:
        """Loads model and weights into memory."""
        print(f"[UniversalTTS] Inicjalizacja modelu: {self.model_name_or_path} na urzÄ…dzeniu: {self.device}...")
        backend = self._select_backend()
        success = backend.load(self.model_name_or_path, self.device)

        if success:
            self._backend = backend
            self.sample_rate = backend.get_sample_rate()
            self._loaded = True
            print(
                f"[UniversalTTS] Uniwersalny silnik TTS gotowy! (Model: {self.model_name_or_path}, SR: {self.sample_rate} Hz)"
            )
        else:
            print(f"[UniversalTTS] Nie udaĹ‚o siÄ™ zaĹ‚adowaÄ‡ modelu {self.model_name_or_path}.")
            if self.fallback_synth is not None:
                self.fallback_synth.load_model()
                self._loaded = self.fallback_synth.is_loaded()
            else:
                self._loaded = False

    def unload_model(self) -> None:
        """Unloads model and releases VRAM memory from the accelerator."""
        print(f"[UniversalTTS] Zwalnianie modelu: {self.model_name_or_path} z pamiÄ™ci VRAM...")
        if self._backend is not None:
            self._backend.unload()
            self._backend = None
        if self.fallback_synth is not None:
            self.fallback_synth.unload_model()
        self._loaded = False
        if torch is not None and torch.cuda.is_available():
            import gc

            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

    def synthesize_segment(self, text: str, lang: str = "pl") -> AudioBuffer:
        """Synthesizes single text segment into AudioBuffer float32."""
        clean_text = text.strip()
        if not clean_text:
            return make_audio_buffer(np.zeros(0, dtype=np.float32))

        voice_str = str(self.reference_voice_path) if self.reference_voice_path else None
        cached_audio = self.cache.get(
            text=clean_text,
            lang=lang,
            voice=voice_str,
            temperature=self.temperature,
            cfg_weight=self.cfg_weight,
        )
        if cached_audio is not None and len(cached_audio) > 0:
            return cached_audio

        if self._backend is not None:
            try:
                ref_str: Optional[str] = None
                if self.reference_voice_path and Path(self.reference_voice_path).exists():
                    ref_str = str(self.reference_voice_path)

                audio_np = self._backend.generate(
                    text=clean_text,
                    lang=lang,
                    reference_audio_path=ref_str,
                    speed=self.speed,
                    temperature=self.temperature,
                    cfg_weight=self.cfg_weight,
                    exaggeration=self.exaggeration,
                    repetition_penalty=self.repetition_penalty,
                )

                if self.trim_trailing_silence and len(audio_np) > 0:
                    audio_buf = make_audio_buffer(np.asarray(audio_np, dtype=np.float32))
                    cleaned = self.cleaner.clean_tail(audio_buf, sample_rate=self.sample_rate)
                    audio_np = np.asarray(cleaned, dtype=np.float32)

                if len(audio_np) > 0:
                    audio_buf = make_audio_buffer(np.asarray(audio_np, dtype=np.float32))
                    self.cache.put(
                        text=clean_text,
                        audio=audio_buf,
                        lang=lang,
                        voice=voice_str,
                        temperature=self.temperature,
                        cfg_weight=self.cfg_weight,
                        sample_rate=self.sample_rate,
                    )

                return make_audio_buffer(np.asarray(audio_np, dtype=np.float32))
            except Exception as e:
                print(f"[UniversalTTS] BĹ‚Ä…d generowania mowy ('{clean_text[:35]}...'): {e}")

        if self.fallback_synth is not None:
            return self.fallback_synth.synthesize_segment(clean_text, lang=lang)

        return make_audio_buffer(np.zeros(0, dtype=np.float32))


# ============================================================================
# Implementation note: see the surrounding code for the behavior described here.
# ============================================================================

UniversalSynthesizerAdapter = UniversalTTSEngine
OmniVoiceTTSEngine = UniversalTTSEngine
ChatterboxTTSEngine = UniversalTTSEngine
ChatterboxSynthesizer = UniversalTTSEngine
OmniVoiceSynthesizer = UniversalTTSEngine

__all__ = [
    "UniversalTTSEngine",
    "UniversalTTSEngineOptions",
    "UniversalSynthesizerAdapter",
    "OmniVoiceTTSEngine",
    "ChatterboxTTSEngine",
    "ChatterboxSynthesizer",
    "OmniVoiceSynthesizer",
    "ModelBackendProtocol",
]
