"""
lektor.adapters.gui.routers.player
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Router handling page player, generation status, page details, and audio streaming.
Dependency Inversion (DIP) with paths injected via FastAPI Depends.
Strict typing without Any.
"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ....application.dtos import BookStatusDTO, PreviewPageQuery
from ....application.use_cases.get_book_status import GetBookStatusUseCase
from ....application.use_cases.preview_page import PreviewPageUseCase
from ....domain.audio_models import LanguageMode
from ..dependencies import (
    get_book_status_use_case,
    get_gui_paths,
    get_preview_page_use_case,
)
from ..paths import GuiPaths
from ..state import (
    get_audio_duration,
    get_page_title,
)

router = APIRouter(tags=["Player"])


@router.get("/api/status", response_model=BookStatusDTO)
def get_status(
    uc: GetBookStatusUseCase = Depends(get_book_status_use_case),
) -> BookStatusDTO:
    """Returns list of all pages with detailed status and generation progress."""
    return uc.execute()


@router.get("/api/page/{page_id}")
def get_page_details(
    page_id: str,
    lang_mode: Optional[str] = None,
    paths: GuiPaths = Depends(get_gui_paths),
    preview_page_uc: PreviewPageUseCase = Depends(get_preview_page_use_case),
) -> dict[str, object]:
    """Returns normalized text and raw page content using PreviewPageUseCase."""
    md_file = paths.pages_dir / f"{page_id}.md"
    txt_file = paths.audio_dir / f"{page_id}_normalized.txt"
    wav_file = paths.audio_dir / f"{page_id}.wav"

    if not md_file.exists():
        raise HTTPException(status_code=404, detail="Page not found")

    raw_text = md_file.read_text(encoding="utf-8") if md_file.exists() else ""
    norm_text = txt_file.read_text(encoding="utf-8") if txt_file.exists() else ""

    selected_mode: LanguageMode = lang_mode.strip().lower() if lang_mode else "bilingual"

    segments: list[str] = []
    try:
        query = PreviewPageQuery(
            markdown_path=md_file,
            raw_text=raw_text,
            language_mode=selected_mode,
        )
        preview_res = preview_page_uc.execute(query)
        segments = [
            f"[{s.lang.upper()}][Pauza: {s.pause_after_ms}ms] {s.text}"
            for s in preview_res.segments
        ]
    except Exception:
        segments = []
        if norm_text:
            for line in norm_text.splitlines():
                line = line.strip()
                if line:
                    segments.append(line)

    has_wav = wav_file.exists() and wav_file.stat().st_size > 1000
    duration = get_audio_duration(wav_file) if has_wav else 0.0

    return {
        "id": page_id,
        "title": get_page_title(md_file),
        "has_wav": has_wav,
        "duration": duration,
        "wav_url": f"/audio/{page_id}.wav" if has_wav else None,
        "segments": segments,
        "raw_text": raw_text,
    }


@router.get("/audio/{filename}")
def stream_audio(
    filename: str,
    paths: GuiPaths = Depends(get_gui_paths),
) -> FileResponse:
    """Serves WAV audio file with support for HTTP Range headers (audio seeking)."""
    safe_name = Path(filename).name
    wav_path = (paths.audio_dir / safe_name).resolve()
    if not wav_path.is_relative_to(paths.audio_dir.resolve()) or not wav_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(
        path=wav_path,
        media_type="audio/wav",
        filename=safe_name,
    )
