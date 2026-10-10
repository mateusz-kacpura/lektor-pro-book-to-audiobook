"""
lektor.adapters.gui.routers.studio
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Router handling Markdown TTS Studio (arbitrary Markdown synthesis, history, deletion).
Dependency Inversion (DIP) with Use Cases and Repositories injected via FastAPI Depends.
Strict typing without Any.
"""

import logging
import re
import time
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from ....application.dtos import SynthesizeSnippetCommand
from ....application.ports.storage_ports import StudioHistoryRepositoryProtocol
from ....application.ports.telemetry_ports import GpuTelemetryProtocol
from ....application.use_cases.synthesize_snippet import SynthesizeMarkdownSnippetUseCase
from ....domain.languages import LanguagePair, TTSProvider, language_options
from ....domain.normalizers.markdown import extract_markdown_title
from ....domain.studio_models import StudioItem
from ..dependencies import (
    get_gpu_telemetry,
    get_gui_paths,
    get_studio_history_repository,
    get_synthesize_snippet_use_case,
)
from ..paths import GuiPaths
from ..schemas import StudioSynthesizeRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Studio"])


def _synthesis_stats(history: Sequence[StudioItem]) -> dict[str, object]:
    """Calculates completed synthesis statistics based on Studio history."""
    durations = [item.synth_time_sec for item in history if item.synth_time_sec > 0]
    return {
        "last_synthesis_sec": round(durations[0], 2) if durations else None,
        "average_synthesis_sec": round(sum(durations) / len(durations), 2) if durations else None,
        "completed_syntheses": len(durations),
    }


@router.get("/studio", response_class=HTMLResponse)
def studio_page(
    request: Request,
    paths: GuiPaths = Depends(get_gui_paths),
) -> HTMLResponse:
    """Podstrona Markdown TTS Studio."""
    template_path = paths.templates_dir / "studio.html"
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Szablon studio.html nie istnieje")

    templates = Jinja2Templates(directory=str(paths.templates_dir))
    return templates.TemplateResponse(request=request, name="studio.html")


@router.get("/api/languages")
def get_languages(provider: str = "omnivoice") -> dict[str, object]:
    """Returns list of languages supported by the selected TTS model."""
    if provider not in ("omnivoice", "chatterbox"):
        raise HTTPException(status_code=400, detail="Nieobs?ugiwany dostawca TTS.")
    selected_provider = cast(TTSProvider, provider)
    return {"items": language_options(provider=selected_provider)}


@router.get("/api/studio/history")
def get_studio_history(
    history_repo: StudioHistoryRepositoryProtocol = Depends(get_studio_history_repository),
) -> dict[str, object]:
    """Returns list of recorded Studio TTS audio items from repository."""
    history = history_repo.get_history()
    items = [it.to_dict() if isinstance(it, StudioItem) else it for it in history]
    return {"items": items, "count": len(items), "stats": _synthesis_stats(history)}


@router.get("/api/studio/stats")
def get_studio_stats(
    gpu_telemetry: GpuTelemetryProtocol = Depends(get_gpu_telemetry),
    history_repo: StudioHistoryRepositoryProtocol = Depends(get_studio_history_repository),
) -> dict[str, object]:
    """Returns current GPU telemetry and Studio synthesis metrics."""
    try:
        used_vram_mb, total_vram_mb, gpu_utilization_pct = gpu_telemetry.get_gpu_stats()
    except Exception:
        logger.warning("Nie udało się odczytać telemetrii GPU dla Studio", exc_info=True)
        used_vram_mb, total_vram_mb, gpu_utilization_pct = 0.0, 0.0, 0.0

    return {
        "gpu": {
            "used_vram_mb": round(used_vram_mb, 1),
            "total_vram_mb": round(total_vram_mb, 1),
            "utilization_pct": round(gpu_utilization_pct, 1),
        },
        "stats": _synthesis_stats(history_repo.get_history()),
    }


@router.post("/api/studio/synthesize")
def studio_synthesize(
    req: StudioSynthesizeRequest,
    paths: GuiPaths = Depends(get_gui_paths),
    history_repo: StudioHistoryRepositoryProtocol = Depends(get_studio_history_repository),
    synthesize_snippet_uc: SynthesizeMarkdownSnippetUseCase = Depends(get_synthesize_snippet_use_case),
) -> dict[str, object]:
    """Processes Markdown, normalizes text, and synthesizes audio via use case."""
    raw_md = req.markdown.strip()
    if not raw_md:
        raise HTTPException(status_code=400, detail="Tekst Markdown jest pusty.")

    item_id = req.id if (req.id and req.id.strip()) else f"tts_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "", item_id)
    wav_name = f"{safe_id}.wav"
    wav_path = paths.studio_audio_dir / wav_name

    history = list(history_repo.get_history())
    existing_item = next((it for it in history if it.id == safe_id), None)
    if not req.force and wav_path.exists() and wav_path.stat().st_size > 1000 and existing_item:
        return {
            "status": "ready",
            "item": existing_item.to_dict() if isinstance(existing_item, StudioItem) else existing_item,
        }

    language_pair = LanguagePair(
        primary=req.primary_language,
        secondary=req.secondary_language,
    )
    cmd = SynthesizeSnippetCommand(
        snippet_id=safe_id,
        markdown=raw_md,
        output_path=wav_path,
        language_mode=req.lang,
        language_pair=language_pair,
        force=req.force,
        voice_path=paths.default_voice if paths.default_voice.exists() else None,
        temperature=req.temperature if req.temperature is not None else 0.33,
        cfg_weight=req.cfg_weight if req.cfg_weight is not None else 0.68,
    )

    try:
        t0 = time.time()
        result = synthesize_snippet_uc.execute(cmd)
        synth_duration = round(time.time() - t0, 2)
    except Exception as e:
        logger.error(f"[Studio Synthesize Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))

    title = req.title.strip() if (req.title and req.title.strip()) else extract_markdown_title(raw_md)
    t_stamp = int(time.time())

    item = StudioItem(
        id=safe_id,
        title=title,
        markdown=raw_md,
        normalized_preview="\n".join(result.normalized_preview[:5]),
        segments_count=result.segment_count,
        lang=f"{language_pair.primary}+{language_pair.secondary or ''}",
        speed=req.speed,
        filename=wav_name,
        audio_url=f"/audio/studio/{wav_name}?t={t_stamp}",
        audio_exists=True,
        duration_sec=result.duration_sec,
        file_size_kb=result.file_size_kb,
        synth_time_sec=synth_duration,
        created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )

    history_repo.add_or_update_item(item)

    return {
        "status": "regenerated" if req.force else "generated",
        "item": item.to_dict(),
    }


@router.delete("/api/studio/item/{item_id}")
def delete_studio_item(
    item_id: str,
    history_repo: StudioHistoryRepositoryProtocol = Depends(get_studio_history_repository),
) -> dict[str, object]:
    """Deletes audio recording from disk and removes entry from history repository."""
    safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "", item_id)
    history_repo.delete_item(safe_id)
    return {"status": "deleted", "id": safe_id}


@router.get("/audio/studio/{filename}")
def stream_studio_audio(
    filename: str,
    paths: GuiPaths = Depends(get_gui_paths),
) -> FileResponse:
    """Serwuje wygenerowany plik WAV ze Studio TTS (inline streaming)."""
    safe_name = Path(filename).name
    wav_path = (paths.studio_audio_dir / safe_name).resolve()
    if not wav_path.is_relative_to(paths.studio_audio_dir.resolve()) or not wav_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path=wav_path, media_type="audio/wav", content_disposition_type="inline")
