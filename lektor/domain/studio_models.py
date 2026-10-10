"""
lektor.domain.studio_models
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Value Object representing generated recordings in the Markdown TTS Studio module.
Strict typing without Any.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StudioItem:
    """Value Object representing a synthesized recording item in Markdown TTS Studio."""
    id: str
    title: str
    markdown: str
    normalized_preview: str = ""
    segments_count: int = 0
    lang: str = "pl"
    speed: float = 1.0
    filename: str = ""
    audio_url: str = ""
    audio_exists: bool = False
    duration_sec: float = 0.0
    file_size_kb: float = 0.0
    synth_time_sec: float = 0.0
    created_at: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "markdown": self.markdown,
            "normalized_preview": self.normalized_preview,
            "segments_count": self.segments_count,
            "lang": self.lang,
            "speed": self.speed,
            "filename": self.filename,
            "audio_url": self.audio_url,
            "audio_exists": self.audio_exists,
            "duration_sec": self.duration_sec,
            "file_size_kb": self.file_size_kb,
            "synth_time_sec": self.synth_time_sec,
            "created_at": self.created_at,
        }

    def __getitem__(self, key: str) -> object:
        return getattr(self, key)

    def get(self, key: str, default: object = None) -> object:
        return getattr(self, key, default)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "StudioItem":
        safe_id = str(data.get("id", ""))
        title = str(data.get("title", ""))
        markdown = str(data.get("markdown", ""))
        preview = str(data.get("normalized_preview", ""))
        seg_raw = data.get("segments_count", 0)
        segments_count = int(seg_raw) if isinstance(seg_raw, (int, float)) else 0
        lang = str(data.get("lang", "pl"))
        speed_raw = data.get("speed", 1.0)
        speed = float(speed_raw) if isinstance(speed_raw, (int, float)) else 1.0
        filename = str(data.get("filename", ""))
        audio_url = str(data.get("audio_url", ""))
        audio_exists = bool(data.get("audio_exists", False))
        dur_raw = data.get("duration_sec", 0.0)
        duration_sec = float(dur_raw) if isinstance(dur_raw, (int, float)) else 0.0
        size_raw = data.get("file_size_kb", 0.0)
        file_size_kb = float(size_raw) if isinstance(size_raw, (int, float)) else 0.0
        synth_raw = data.get("synth_time_sec", 0.0)
        synth_time_sec = float(synth_raw) if isinstance(synth_raw, (int, float)) else 0.0
        created_at = str(data.get("created_at", ""))

        return cls(
            id=safe_id,
            title=title,
            markdown=markdown,
            normalized_preview=preview,
            segments_count=segments_count,
            lang=lang,
            speed=speed,
            filename=filename,
            audio_url=audio_url,
            audio_exists=audio_exists,
            duration_sec=duration_sec,
            file_size_kb=file_size_kb,
            synth_time_sec=synth_time_sec,
            created_at=created_at,
        )
