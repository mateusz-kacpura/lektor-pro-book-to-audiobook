# pyright: reportMissingTypeStubs=none
"""
lektor.adapters.audio.cleaner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Audio cleaning adapter implementing AudioCleanerProtocol (DIP).
Eliminates speech artifacts, background noise, and vocoder distortion.
"""

from typing import Optional, Sequence

import librosa
import numpy as np
import scipy.signal as signal  # pyright: ignore[reportMissingTypeStubs]
import torch
import torchaudio

try:
    import noisereduce as nr
except ImportError:
    nr = None

from ...application.ports.audio_ports import AudioCleanerProtocol
from ...domain.audio_models import AudioBuffer, make_audio_buffer


class SileroAudioCleaner(AudioCleanerProtocol):
    """Audio cleaning adapter eliminating speech artifacts, vocoder hum, and background noise."""

    def __init__(
        self,
        sample_rate: int = 24000,
        highpass_cutoff_hz: float = 75.0,
        noise_reduction_prop: float = 0.65,
    ) -> None:
        self.sample_rate = sample_rate
        self.highpass_cutoff_hz = highpass_cutoff_hz
        self.noise_reduction_prop = noise_reduction_prop
        self._vad_model: Optional[object] = None
        self._vad_utils: Optional[Sequence[object]] = None

    def get_vad_model(self) -> tuple[Optional[object], Optional[Sequence[object]]]:
        """Lazily loads the Silero VAD model for speech boundary detection."""
        if self._vad_model is None and torch is not None:
            try:
                m, u = torch.hub.load("snakers4/silero-vad", "silero_vad", trust_repo=True)
                self._vad_model = m
                self._vad_utils = u if isinstance(u, (list, tuple)) else None
            except Exception:
                self._vad_model = False
        return self._vad_model, self._vad_utils

    def clean_tail(self, audio: AudioBuffer, sample_rate: int = 24000) -> AudioBuffer:
        """Cleans audio buffer of trailing noise, clicks, and vocoder artifacts."""
        sr = sample_rate if sample_rate > 0 else self.sample_rate
        if len(audio) < sr * 0.2:
            return audio

        filtered = self._apply_highpass_filter(np.asarray(audio, dtype=np.float32), sr)
        trimmed = self._trim_boundaries(filtered, sr)
        reduced = self._apply_noise_reduction(trimmed, sr)
        faded = self._apply_fades(reduced, sr)

        return make_audio_buffer(np.asarray(faded, dtype=np.float32))

    def _apply_highpass_filter(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """1. High-pass filter (4th-order Butterworth) eliminating subsonic rumble."""
        if signal is not None:
            try:
                b, a = signal.butter(4, self.highpass_cutoff_hz, btype="highpass", fs=sr)
                filtered = signal.filtfilt(b, a, audio)
                return np.asarray(filtered, dtype=np.float32)
            except Exception:
                pass
        return audio

    def _trim_boundaries(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """2. Trims speech boundary artifacts using Silero VAD or energy detection."""
        trimmed_audio, success = self._trim_with_vad(audio, sr)
        if success:
            return trimmed_audio
        return self._trim_with_rms(audio, sr)

    def _trim_with_vad(self, audio: np.ndarray, sr: int) -> tuple[np.ndarray, bool]:
        """Attempts to trim audio using the Silero VAD model."""
        if torch is None or torchaudio is None:
            return audio, False

        try:
            vad_model, vad_utils = self.get_vad_model()
            if not vad_model or not vad_utils or len(vad_utils) == 0:
                return audio, False

            fn = vad_utils[0]
            if not callable(fn):
                return audio, False

            audio_tensor = torch.from_numpy(audio).float()
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
            audio_16k = resampler(audio_tensor)
            timestamps = fn(
                audio_16k,
                vad_model,
                sampling_rate=16000,
                threshold=0.45,
                min_speech_duration_ms=80,
                min_silence_duration_ms=180,
                speech_pad_ms=75,
            )
            if isinstance(timestamps, list) and len(timestamps) > 0:
                scale = sr / 16000
                first_ts = timestamps[0]
                last_ts = timestamps[-1]
                if isinstance(first_ts, dict) and isinstance(last_ts, dict):
                    start_val = int(first_ts.get("start", 0))
                    end_val = int(last_ts.get("end", len(audio)))
                    start_sample = max(0, int(start_val * scale) - int(sr * 0.03))
                    end_sample = min(len(audio), int(end_val * scale) + int(sr * 0.065))
                    return audio[start_sample:end_sample], True
        except Exception:
            pass

        return audio, False

    def _trim_with_rms(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Fallback odcinania ogona mowy oparty na energii RMS (librosa)."""
        if librosa is not None:
            try:
                frame_len = int(sr * 0.02)
                hop_len = int(sr * 0.01)
                rms = librosa.feature.rms(y=audio, frame_length=frame_len, hop_length=hop_len)[0]
                peak_rms = float(np.max(rms))
                if peak_rms > 0:
                    threshold = peak_rms * 0.06
                    voiced_frames = np.where(rms > threshold)[0]
                    if len(voiced_frames) > 0:
                        last_sample = min(len(audio), int((voiced_frames[-1] + 4) * hop_len))
                        return audio[:last_sample]
            except Exception:
                pass
        return audio

    def _apply_noise_reduction(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """3. Background noise reduction (noisereduce)."""
        if nr is not None:
            try:
                reduced = nr.reduce_noise(
                    y=audio,
                    sr=sr,
                    prop_decrease=self.noise_reduction_prop,
                    stationary=True,
                )
                return np.asarray(reduced, dtype=np.float32)
            except Exception:
                pass
        return audio

    def _apply_fades(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """4. Edge smoothing with fade-in (15ms) and fade-out (35ms)."""
        fade_in = int(sr * 0.015)
        if len(audio) > fade_in:
            audio[:fade_in] *= np.linspace(0, 1, fade_in)

        fade_out = int(sr * 0.035)
        if len(audio) > fade_out:
            fade = np.cos(np.linspace(0, np.pi / 2, fade_out)) ** 2
            audio[-fade_out:] *= fade

        return audio
