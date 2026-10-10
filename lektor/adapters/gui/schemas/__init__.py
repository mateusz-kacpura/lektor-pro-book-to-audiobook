"""
lektor.adapters.gui.schemas
"""

from typing import Optional

from pydantic import BaseModel


class GenerationParams(BaseModel):
    temperature: float = 0.33
    cfg_weight: float = 0.68
    exaggeration: float = 0.25
    repetition_penalty: float = 1.8
    voice_path: str = ""
    language_mode: str = "bilingual"
    input_language: str = "auto"


class NoteSaveRequest(BaseModel):
    note_id: str = "global"
    content: str


class StudioSynthesizeRequest(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    markdown: str
    lang: str = "bilingual"
    primary_language: str = "pl"
    secondary_language: Optional[str] = "en"
    speed: float = 1.0
    force: bool = False
    temperature: Optional[float] = None
    cfg_weight: Optional[float] = None
    exaggeration: Optional[float] = None


__all__ = [
    "GenerationParams",
    "NoteSaveRequest",
    "StudioSynthesizeRequest",
]
