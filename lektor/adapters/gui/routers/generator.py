"""
lektor.adapters.gui.routers.generator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Router handling page regeneration and batch processing (Batch).
Dependency Inversion (DIP) with application Use Cases and injected JobExecutionManager.
Strict typing without Any.
"""

import re
import threading
import time
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ....application.dtos import BatchSynthesisCommand, SynthesizePageCommand
from ....application.ports.storage_ports import PageRepositoryProtocol
from ....application.ports.telemetry_ports import GpuTelemetryProtocol, ProgressReporterProtocol
from ....application.use_cases.batch_synthesis import BatchSynthesisUseCase
from ....application.use_cases.synthesize_page import SynthesizePageUseCase
from ....domain.audio_models import SynthesisResult
from ....domain.languages import LanguagePair, get_language_spec
from ..dependencies import (
    get_gpu_telemetry,
    get_gui_paths,
    get_job_manager,
    get_page_repository,
    get_synthesize_page_use_case,
)
from ..job_manager import JobExecutionManager
from ..paths import GuiPaths
from ..schemas import GenerationParams

router = APIRouter(tags=["Generator"])


def _language_pair_from_params(params: GenerationParams) -> LanguagePair | None:
    """Builds language pair configuration from batch generator request."""
    selected = params.input_language.strip().casefold()
    if selected in {"", "auto"}:
        legacy_mode = params.language_mode.strip().casefold()
        if legacy_mode in {"", "bilingual"}:
            return None
        selected = legacy_mode

    if not re.fullmatch(r"[a-z]{2,3}(?:-[a-z]{2,4})?", selected):
        raise HTTPException(status_code=422, detail=f"Nieprawidłowy kod języka wejściowego: {selected!r}")

    try:
        language = get_language_spec(selected, allow_custom=True)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return LanguagePair(primary=language.code, secondary=None)


class GuiBatchProgressReporter(ProgressReporterProtocol):
    """Batch operation progress reporting adapter for Web GUI state."""

    def __init__(self, audio_dir: Path, job_mgr: JobExecutionManager, gpu_telemetry: GpuTelemetryProtocol) -> None:
        self._audio_dir = audio_dir
        self._job_mgr = job_mgr
        self._gpu = gpu_telemetry
        self._page_started_at = 0.0
        self._completed_pages = 0
        self._total_page_time_sec = 0.0
        self._last_page_duration_sec = 0.0
    def on_page_start(self, page_path: Path, current_idx: int, total_pages: int) -> None:
        self._job_mgr.set_active_generation(page_path.stem)
        self._page_started_at = time.perf_counter()
        used_vram, total_vram, gpu_util = self._gpu.get_gpu_stats()
        pct = round(((current_idx - 1) / max(1, total_pages)) * 100, 1)
        print(f"\n[Batch Generator] [{current_idx}/{total_pages}] Generowanie: {page_path.name}")
        state_file = self._audio_dir / ".generator_state.json"
        state_data: dict[str, object] = {
            "page_id": page_path.stem,
            "filename": page_path.name,
            "current_idx": current_idx,
            "total_pages": total_pages,
            "percentage": pct,
            "timestamp": time.time(),
            "status": "generating",
            "current_sentence": f"Synteza strony {page_path.stem} na GPU...",
            "last_page_duration_sec": self._last_page_duration_sec,
            "average_page_duration_sec": self._total_page_time_sec / self._completed_pages
            if self._completed_pages
            else 0.0,
            "vram_used_mb": used_vram,
            "vram_total_mb": total_vram,
            "gpu_utilization_pct": gpu_util,
        }
        try:
            import json

            state_file.write_text(json.dumps(state_data), encoding="utf-8")
        except Exception:
            pass

    def on_page_complete(self, result: SynthesisResult) -> None:
        duration = max(time.perf_counter() - self._page_started_at, 0.01)
        self._completed_pages += 1
        self._total_page_time_sec += duration
        self._last_page_duration_sec = duration
        used_vram, total_vram, gpu_util = self._gpu.get_gpu_stats()
        self._job_mgr.set_active_generation(None)
        print(f"[Batch Generator] Ukończono stronę: {result.audio_path.name}")
        state_file = self._audio_dir / ".generator_state.json"
        state_data: dict[str, object] = {
            "page_id": result.audio_path.stem,
            "status": "completed",
            "timestamp": time.time(),
            "last_page_duration_sec": duration,
            "average_page_duration_sec": self._total_page_time_sec / self._completed_pages,
            "vram_used_mb": used_vram,
            "vram_total_mb": total_vram,
            "gpu_utilization_pct": gpu_util,
        }
        try:
            import json

            state_file.write_text(json.dumps(state_data), encoding="utf-8")
        except Exception:
            pass

    def on_skipped(self, page_path: Path, reason: str) -> None:
        self._job_mgr.set_active_generation(None)
        print(f"[Batch Generator] Pominięto {page_path.name}: {reason}")

    def on_error(self, page_path: Path, error: Exception) -> None:
        self._job_mgr.set_active_generation(None)
        print(f"[Batch Generator] Błąd na stronie {page_path.name}: {error}")

    def check_cancellation(self) -> bool:
        cancelled = self._job_mgr.is_batch_cancelled()
        if cancelled:
            print("[Batch Generator] Wykryto sygnał zatrzymania zadania wsadowego.")
        return cancelled


def run_regeneration_task(
    page_id: str,
    paths: GuiPaths,
    use_case: SynthesizePageUseCase,
    job_mgr: JobExecutionManager,
    language_pair: LanguagePair | None,
) -> None:
    """Executes page regeneration using SynthesizePageUseCase."""
    job_mgr.set_active_generation(page_id)
    try:
        md_file = paths.pages_dir / f"{page_id}.md"
        cmd = SynthesizePageCommand(
            markdown_path=md_file,
            output_dir=paths.audio_dir,
            skip_existing=False,
            save_normalized_text=True,
            audio_format="wav",
            language_pair=language_pair,
        )
        use_case.execute(cmd)
    except Exception as e:
        print(f"[GUI Server] Błąd regeneracji strony {page_id}: {e}")
    finally:
        job_mgr.set_active_generation(None)


@router.post("/api/regenerate/{page_id}")
def regenerate_page(
    page_id: str,
    params: GenerationParams,
    background_tasks: BackgroundTasks,
    paths: GuiPaths = Depends(get_gui_paths),
    synthesize_page_uc: SynthesizePageUseCase = Depends(get_synthesize_page_use_case),
    job_mgr: JobExecutionManager = Depends(get_job_manager),
) -> dict[str, object]:
    """Dispatches page regeneration in a background worker."""
    job_mgr.set_current_params(params)
    language_pair = _language_pair_from_params(params)
    md_file = paths.pages_dir / f"{page_id}.md"
    if not md_file.exists():
        raise HTTPException(status_code=404, detail="Strona nie istnieje")

    background_tasks.add_task(run_regeneration_task, page_id, paths, synthesize_page_uc, job_mgr, language_pair)
    return {"status": "started", "page_id": page_id, "params": params.model_dump()}


def run_batch_generation_task(
    params: GenerationParams,
    paths: GuiPaths,
    synthesize_page_uc: SynthesizePageUseCase,
    page_repo: PageRepositoryProtocol,
    job_mgr: JobExecutionManager,
    gpu_telemetry: GpuTelemetryProtocol,
    language_pair: LanguagePair | None,
) -> None:
    """Executes batch synthesis of missing pages using BatchSynthesisUseCase."""
    try:
        print("\n" + "=" * 70)
        print("  [*] [Batch Generator] Rozpoczynam wsadowe generowanie audiobooka...")
        print(f"  - Parametry: temp={params.temperature}, cfg={params.cfg_weight}, exaggeration={params.exaggeration}")
        print("=" * 70)

        reporter = GuiBatchProgressReporter(audio_dir=paths.audio_dir, job_mgr=job_mgr, gpu_telemetry=gpu_telemetry)
        batch_uc = BatchSynthesisUseCase(
            synthesize_page_uc=synthesize_page_uc,
            page_repository=page_repo,
            progress_reporter=reporter,
        )
        cmd = BatchSynthesisCommand(
            pages_dir=paths.pages_dir,
            output_dir=paths.audio_dir,
            pattern="page_*.md",
            skip_existing=True,
            save_normalized_text=True,
            audio_format="wav",
            language_pair=language_pair,
        )
        batch_uc.execute(cmd)
    except Exception as e:
        import traceback

        print(f"[Batch Generator] BLAD podczas syntezy: {e}")
        traceback.print_exc()
    finally:
        job_mgr.reset_batch_state()
        state_file = paths.audio_dir / ".generator_state.json"
        if state_file.exists():
            try:
                state_file.unlink()
            except Exception:
                pass


@router.post("/api/batch/start")
def start_batch_generation(
    params: GenerationParams,
    paths: GuiPaths = Depends(get_gui_paths),
    synthesize_page_uc: SynthesizePageUseCase = Depends(get_synthesize_page_use_case),
    page_repo: PageRepositoryProtocol = Depends(get_page_repository),
    job_mgr: JobExecutionManager = Depends(get_job_manager),
    gpu_telemetry: GpuTelemetryProtocol = Depends(get_gpu_telemetry),
) -> dict[str, object]:
    """Dispatches batch processing of missing pages in a background worker."""
    language_pair = _language_pair_from_params(params)
    if job_mgr.is_batch_running():
        thread = job_mgr.get_batch_thread()
        if thread is not None and thread.is_alive():
            raise HTTPException(status_code=409, detail="Generowanie jest już w toku!")
        job_mgr.reset_batch_state()

    state_file = paths.audio_dir / ".generator_state.json"
    if state_file.exists():
        try:
            state_file.unlink()
        except Exception:
            pass

    batch_thread = threading.Thread(
        target=run_batch_generation_task,
        args=(params, paths, synthesize_page_uc, page_repo, job_mgr, gpu_telemetry, language_pair),
        daemon=True,
    )
    job_mgr.start_batch(batch_thread, params=params)
    return {"status": "started", "message": "Rozpoczęto przetwarzanie wsadowe w tle."}


@router.post("/api/batch/stop")
def stop_batch_generation(
    paths: GuiPaths = Depends(get_gui_paths),
    job_mgr: JobExecutionManager = Depends(get_job_manager),
) -> dict[str, object]:
    """Sends stop signal to the active batch generation loop."""
    job_mgr.stop_batch()
    if not job_mgr.is_batch_running() and not job_mgr.get_active_generation():
        state_file = paths.audio_dir / ".generator_state.json"
        if state_file.exists():
            try:
                state_file.unlink()
            except Exception:
                pass
        return {"status": "not_running", "message": "Generowanie wsadowe nie jest aktywne."}
    return {"status": "stopping", "message": "Zatrzymywanie generowania..."}
