"""
lektor.adapters.gui.state
~~~~~~~~~~~~~~~~~~~~~~~~~
Runtime state management and helper functions for Web GUI server.
Strict typing without Any.
"""

import time
from pathlib import Path
from typing import Optional, Sequence

import soundfile as sf

from ...application.ports.audio_ports import TTSEngineProtocol
from ...application.ports.container_ports import ApplicationContainerProtocol
from ...domain.normalizers.markdown import extract_markdown_title
from .job_manager import JobExecutionManager


def get_page_title(md_file: Path) -> str:
    fallback = md_file.stem.replace("_", " ").title()
    try:
        content = md_file.read_text(encoding="utf-8")
        return extract_markdown_title(content, fallback_title=fallback)
    except Exception:
        return fallback


def get_audio_duration(wav_path: Path) -> float:
    try:
        info = sf.info(str(wav_path))
        return float(info.duration)
    except Exception:
        return 0.0


def parse_active_task_stage(active_page_id: str, audio_dir: Path) -> Optional[dict[str, object]]:
    state_file = audio_dir / ".generator_state.json"
    if state_file.exists():
        try:
            import json
            data = json.loads(state_file.read_text(encoding="utf-8"))
            if data.get("page_id") == active_page_id and (time.time() - float(str(data.get("timestamp", 0.0))) < 180):
                completed = int(data.get("completed_segments", 0))
                total = int(data.get("total_segments", 1))
                current_seg = int(data.get("current_segment") or min(total, completed + 1))
                pct = float(data.get("segment_percent", data.get("percentage", 0.0)))
                sentence = str(data.get("current_sentence") or data.get("current_segment_text") or "Trwa synteza segmentu...")
                stage_desc = str(data.get("stage_description") or f"Synteza mowy: segment {current_seg} z {total} ({pct}%)")
                return {
                    "current_segment": current_seg,
                    "total_segments": total,
                    "completed_segments": completed,
                    "segment_percent": round(pct, 1),
                    "current_sentence": sentence,
                    "stage_description": stage_desc,
                }
        except Exception:
            pass
    return None


def get_generator_info(
    all_pages: Sequence[Path],
    audio_dir: Path,
    job_mgr: Optional[JobExecutionManager] = None,
) -> dict[str, object]:
    """Returns dictionary of audio generator state information for the player."""
    is_batch = job_mgr.is_batch_running() if job_mgr is not None else False
    is_stopping = job_mgr.is_stopping() if job_mgr is not None else False
    active_gen = job_mgr.get_active_generation() if job_mgr is not None else None

    state_file = audio_dir / ".generator_state.json"
    state_is_recent = False
    if state_file.exists():
        try:
            import json
            raw_content = state_file.read_text(encoding="utf-8")
            data = json.loads(raw_content)
            if isinstance(data, dict):
                ts = float(str(data.get("timestamp", 0.0)))
                if time.time() - ts < 180:
                    state_is_recent = True
                    if not active_gen and data.get("page_id"):
                        active_gen = str(data.get("page_id"))
        except Exception:
            pass

    is_active = is_batch or (active_gen is not None) or state_is_recent
    return {
        "is_active": is_active,
        "active_generation": active_gen,
        "is_batch_running": is_batch,
        "is_stopping": is_stopping,
        "total_pages": len(all_pages),
    }


def get_interview_synth(container: ApplicationContainerProtocol) -> TTSEngineProtocol:
    """
    Retrieves TTS engine instance from ApplicationContainerProtocol.
    Enforces container dependency injection (no hidden singletons).
    """
    return container.get_tts_engine()


__all__ = [
    "get_audio_duration",
    "get_generator_info",
    "get_interview_synth",
    "get_page_title",
    "parse_active_task_stage",
]