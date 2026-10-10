"""
lektor.adapters.audio.stitcher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Audio stitching adapter implementing AudioStitcherProtocol (DIP).
Combines synthesized speech segments and pauses using NumPy and SoundFile.
"""

from pathlib import Path
from typing import Sequence

import numpy as np
import soundfile as sf

from ...application.ports.audio_ports import AudioStitcherProtocol
from ...domain.audio_models import AudioBuffer, make_audio_buffer


class NumpyAudioStitcher(AudioStitcherProtocol):
    """Audio stitching and export processor implementing AudioStitcherProtocol."""

    def __init__(self, sample_rate: int = 24000) -> None:
        self.sample_rate = sample_rate

    def create_silence(self, duration_ms: int) -> AudioBuffer:
        """Creates silence buffer for the specified duration."""
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)
        return make_audio_buffer(np.zeros(num_samples, dtype=np.float32))

    def stitch_segments(
        self,
        audio_segments: Sequence[tuple[AudioBuffer | Sequence[float], int]]
    ) -> AudioBuffer:
        """Concatenates speech segments and inter-segment silence into a continuous stream."""
        combined: list[np.ndarray] = []
        for chunk, pause_ms in audio_segments:
            if chunk is not None and len(chunk) > 0:
                chunk_arr = np.asarray(chunk, dtype=np.float32)
                combined.append(chunk_arr)
                if pause_ms > 0:
                    silence = self.create_silence(pause_ms)
                    combined.append(np.asarray(silence, dtype=np.float32))

        if not combined:
            return make_audio_buffer(np.zeros(0, dtype=np.float32))

        full_audio = np.concatenate(combined)
        return self.normalize_volume(make_audio_buffer(full_audio))

    def normalize_volume(
        self,
        audio: AudioBuffer,
        target_peak: float = 0.95
    ) -> AudioBuffer:
        """Normalizes peak audio volume to avoid clipping."""
        if len(audio) == 0:
            return audio

        audio_array = np.asarray(audio, dtype=np.float32)
        peak = float(np.max(np.abs(audio_array)))
        if peak > 0.0:
            normalized = (audio_array / peak) * target_peak
            return make_audio_buffer(np.asarray(normalized, dtype=np.float32))
        return audio

    def save_audio(
        self,
        audio: AudioBuffer,
        output_path: Path,
        format: str = "wav"
    ) -> Path:
        """Exports audio buffer to a WAV file on disk."""
        out_path = Path(output_path).with_suffix(f".{format}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(out_path), audio, self.sample_rate, subtype="PCM_16")
        return out_path

    def get_duration_sec(self, audio: AudioBuffer | Sequence[float]) -> float:
        """Calculates audio duration in seconds."""
        if self.sample_rate <= 0:
            return 0.0
        return len(audio) / float(self.sample_rate)

    def audio_exists(self, output_path: Path, min_bytes: int = 0) -> bool:
        """Checks if audio file exists and has non-zero size."""
        p = Path(output_path)
        if not p.exists():
            return False
        try:
            return p.stat().st_size >= min_bytes
        except OSError:
            return False

    def get_file_size_kb(self, output_path: Path) -> float:
        """Returns file size in kilobytes."""
        p = Path(output_path)
        if not p.exists():
            return 0.0
        try:
            return round(p.stat().st_size / 1024.0, 1)
        except OSError:
            return 0.0

    def get_file_duration_sec(self, output_path: Path) -> float:
        """Returns duration of existing audio file on disk."""
        try:
            info = sf.info(str(output_path))
            return float(info.duration)
        except Exception:
            return 0.0
