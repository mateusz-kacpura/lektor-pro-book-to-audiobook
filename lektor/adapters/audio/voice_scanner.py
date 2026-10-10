"""Speaker voice file scanner adapter."""

from pathlib import Path

from ...application.ports.audio_ports import VoiceDiscoveryProtocol


class FileSystemVoiceDiscoveryAdapter(VoiceDiscoveryProtocol):
    """Voice scanner discovering available WAV files in voices directory."""

    def __init__(self, data_dir: Path, default_voice: Path) -> None:
        self._data_dir = data_dir
        self._default_voice = default_voice

    def discover_voices(self) -> list[dict[str, str]]:
        """Scans directory and returns available speaker voice names."""
        voices: list[dict[str, str]] = [
            {"name": f"{self._default_voice.name} (Głos domyślny)", "path": str(self._default_voice)}
        ]
        seen_paths = {str(self._default_voice.resolve())}

        voices_dir = self._data_dir / "voices"
        search_dirs = [voices_dir] if voices_dir.exists() else [self._data_dir]

        for s_dir in search_dirs:
            for wav_file in sorted(s_dir.glob("*.wav")):
                resolved = str(wav_file.resolve())
                if resolved in seen_paths or wav_file.name.startswith("page_"):
                    continue
                seen_paths.add(resolved)
                voices.append({
                    "name": f"{wav_file.name} (Próbka)",
                    "path": str(wav_file),
                })
        return voices
