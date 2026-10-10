"""Filesystem audio cache adapter avoiding redundant speech synthesis."""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional, cast

import numpy as np

from ...application.ports.audio_ports import AudioCacheProtocol
from ...domain.audio_models import AudioBuffer, make_audio_buffer, SynthesisConfig


class AudioSegmentCache(AudioCacheProtocol):
    """
    Audio segment cache based on checksums of text and synthesis parameters.
    Implements AudioCacheProtocol.
    """

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir.resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.cache_dir.parent / "manifest.json"
        self._manifest: dict[str, object] = self._load_manifest()

    def _load_manifest(self) -> dict[str, object]:
        if self.manifest_file.exists():
            try:
                loaded = json.loads(self.manifest_file.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    return cast(dict[str, object], loaded)
            except Exception:
                pass
        return {
            "total_items": 0,
            "total_hits": 0,
            "total_saved_seconds": 0.0,
            "entries": cast(dict[str, object], {}),
        }

    def _save_manifest(self) -> None:
        try:
            self.manifest_file.write_text(json.dumps(self._manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"[AudioCache] Błąd zapisu manifestu: {e}")

    def compute_hash(
        self,
        text: str,
        lang: str = "pl",
        voice: Optional[str] = None,
        temperature: float = 0.33,
        cfg_weight: float = 0.68,
    ) -> str:
        """Computes unique SHA-256 hash for given text and voice configuration."""
        norm_text = text.strip().lower()
        voice_str = Path(voice).name if voice else "default"
        key_raw = f"{norm_text}|{lang.lower()}|{voice_str}|{temperature:.2f}|{cfg_weight:.2f}"
        return hashlib.sha256(key_raw.encode("utf-8")).hexdigest()

    def get(
        self,
        text: str,
        lang: str = "pl",
        voice: Optional[str] = None,
        config: Optional[SynthesisConfig] = None,
        temperature: float = 0.35,
        cfg_weight: float = 0.7,
    ) -> Optional[AudioBuffer]:
        """Retrieves cached audio as numpy array or None on cache miss."""
        if not text.strip():
            return None

        if config is not None:
            temperature = config.temperature
            cfg_weight = config.cfg_weight
            if config.reference_voice_path is not None:
                voice = str(config.reference_voice_path)

        h = self.compute_hash(text, lang, voice, temperature, cfg_weight)
        bucket = h[:2]
        target = self.cache_dir / bucket / f"{h}.npy"

        if target.exists() and target.stat().st_size > 100:
            try:
                audio_np = np.load(str(target))
                # Register cache hit
                hits_raw = self._manifest.get("total_hits", 0)
                tot_hits = int(hits_raw) if isinstance(hits_raw, (int, float)) else 0
                self._manifest["total_hits"] = tot_hits + 1

                entries_raw = self._manifest.get("entries")
                if isinstance(entries_raw, dict):
                    entry = entries_raw.get(h)
                    if isinstance(entry, dict):
                        h_count = entry.get("hits", 0)
                        entry["hits"] = (int(h_count) if isinstance(h_count, (int, float)) else 0) + 1
                        entry["last_accessed"] = time.time()
                        duration = entry.get("duration", 0.0)
                        dur_f = float(duration) if isinstance(duration, (int, float)) else 0.0
                        saved_raw = self._manifest.get("total_saved_seconds", 0.0)
                        saved_f = float(saved_raw) if isinstance(saved_raw, (int, float)) else 0.0
                        self._manifest["total_saved_seconds"] = saved_f + dur_f

                return make_audio_buffer(cast(np.ndarray, audio_np))
            except Exception:
                return None
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
        """Saves audio chunk to cache as .npy file."""
        if len(audio) == 0 or not text.strip():
            return

        if config is not None:
            temperature = config.temperature
            cfg_weight = config.cfg_weight
            if config.reference_voice_path is not None:
                voice = str(config.reference_voice_path)

        h = self.compute_hash(text, lang, voice, temperature, cfg_weight)
        bucket = h[:2]
        bucket_dir = self.cache_dir / bucket
        bucket_dir.mkdir(parents=True, exist_ok=True)
        target = bucket_dir / f"{h}.npy"

        try:
            np.save(str(target), np.asarray(audio, dtype=np.float32))

            duration_sec = round(len(audio) / sample_rate, 2)
            entries_raw = self._manifest.get("entries")
            if isinstance(entries_raw, dict):
                entries_raw[h] = {
                    "text": text[:60],
                    "lang": lang,
                    "voice": Path(voice).name if voice else "default",
                    "duration": duration_sec,
                    "created": time.time(),
                    "last_accessed": time.time(),
                    "hits": 0,
                }
            items_raw = self._manifest.get("total_items", 0)
            tot_items = int(items_raw) if isinstance(items_raw, (int, float)) else 0
            self._manifest["total_items"] = tot_items + 1

            if tot_items % 5 == 0:
                self._save_manifest()
        except Exception as e:
            print(f"[AudioCache] Błąd zapisu do cache ({h}): {e}")

    def get_stats(self) -> dict[str, object]:
        """Returns cache efficiency and hit/miss metrics."""
        saved_raw = self._manifest.get("total_saved_seconds", 0.0)
        saved_sec = float(saved_raw) if isinstance(saved_raw, (int, float)) else 0.0
        return {
            "total_items": self._manifest.get("total_items", 0),
            "total_hits": self._manifest.get("total_hits", 0),
            "total_saved_seconds": round(saved_sec, 1),
            "cache_dir": str(self.cache_dir),
        }

