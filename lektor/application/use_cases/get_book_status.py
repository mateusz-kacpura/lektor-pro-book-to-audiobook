"""
lektor.application.use_cases.get_book_status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use case: Retrieving aggregated book, player, and synthesis progress status.
Strict typing without Any.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from ...domain.book_models import Book
from ...domain.normalizers.markdown import extract_markdown_title
from ..dtos import BookStatusDTO, GetBookStatusQuery
from ..ports.audio_ports import AudioStitcherProtocol, VoiceDiscoveryProtocol
from ..ports.storage_ports import BookRepositoryProtocol, PageRepositoryProtocol
from ..ports.telemetry_ports import JobStatusProviderProtocol


def _safe_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _safe_int(value: object, default: int = 0) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


@dataclass(frozen=True)
class _ProcessingState:
    data: dict[str, object]
    active_page: Optional[str]
    is_recent: bool


@dataclass(frozen=True)
class _JobStatus:
    is_batch_running: bool
    is_stopping: bool
    active_generation: Optional[str]
    current_params: dict[str, object]


@dataclass(frozen=True)
class _PageSnapshot:
    pages: list[dict[str, object]]
    ready_ids: set[str]
    total_audio_sec: float
    latest_ready_id: Optional[str]


class GetBookStatusUseCase:
    """
    Use case responsible for retrieving aggregated book and player status.
    Encapsulates queries to page and book repositories and progress metric calculations.
    """

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        page_repository: PageRepositoryProtocol,
        audio_stitcher: AudioStitcherProtocol,
        voice_discovery: Optional[VoiceDiscoveryProtocol] = None,
        job_status_provider: Optional[JobStatusProviderProtocol] = None,
    ) -> None:
        self._book_repo = book_repository
        self._page_repo = page_repository
        self._stitcher = audio_stitcher
        self._voice_discovery = voice_discovery
        self._job_status = job_status_provider

    def execute(self, query: Optional[GetBookStatusQuery] = None) -> BookStatusDTO:
        book = self._resolve_book(query)
        all_pages = tuple(self._page_repo.list_pages(book.paths.pages_dir, pattern="page_*.md"))
        job_status = self._read_job_status()
        processing_state = self._read_processing_state(book.paths.audio_dir / ".generator_state.json")

        is_active = (
            job_status.is_batch_running or job_status.active_generation is not None or processing_state.is_recent
        )
        active_generation = job_status.active_generation or (processing_state.active_page if is_active else None)
        page_snapshot = self._build_page_snapshot(all_pages, book.paths.audio_dir, is_active, active_generation)
        active_page = (
            self._build_active_page(all_pages, book.paths.audio_dir, active_generation, processing_state.data)
            if active_generation and is_active
            else None
        )
        progress = self._build_progress(all_pages, page_snapshot, processing_state, is_active, active_page)

        total_pdf_pages = book.metadata.total_pages or len(page_snapshot.pages)
        available_voices = self._voice_discovery.discover_voices() if self._voice_discovery else []

        return BookStatusDTO(
            book_title=book.metadata.title or book.title,
            total_pdf_pages=total_pdf_pages,
            markdown_pages_count=len(page_snapshot.pages),
            is_batch_running=job_status.is_batch_running,
            is_stopping=job_status.is_stopping,
            total_pages=len(page_snapshot.pages),
            ready_count=len(page_snapshot.ready_ids),
            latest_ready_page=page_snapshot.latest_ready_id,
            active_generation=active_generation if (is_active or job_status.is_batch_running) else None,
            progress=progress,
            current_params=job_status.current_params,
            available_voices=available_voices,
            pages=page_snapshot.pages,
        )

    def _resolve_book(self, query: Optional[GetBookStatusQuery]) -> Book:
        clean_slug = query.book_slug if query and query.book_slug else None
        if clean_slug:
            book = self._book_repo.get_book(clean_slug)
            if book is None:
                raise ValueError(f"Książka '{clean_slug}' nie istnieje.")
            return book
        return self._book_repo.get_active_book()

    def _read_job_status(self) -> _JobStatus:
        if self._job_status is None:
            return _JobStatus(False, False, None, {})
        return _JobStatus(
            is_batch_running=self._job_status.is_batch_running(),
            is_stopping=self._job_status.is_stopping(),
            active_generation=self._job_status.get_active_generation(),
            current_params=self._job_status.get_current_params_dict(),
        )

    def _read_processing_state(self, state_file: Path) -> _ProcessingState:
        if not self._page_repo.page_exists(state_file):
            return _ProcessingState({}, None, False)

        try:
            parsed = json.loads(self._page_repo.read_markdown(state_file))
        except (OSError, UnicodeError, TypeError, ValueError):
            return _ProcessingState({}, None, False)

        if not isinstance(parsed, dict):
            return _ProcessingState({}, None, False)

        timestamp = _safe_float(parsed.get("timestamp"))
        is_recent = time.time() - timestamp < 15
        active_page = str(parsed["page_id"]) if is_recent and parsed.get("page_id") else None
        return _ProcessingState(parsed, active_page, is_recent)

    def _build_page_snapshot(
        self,
        all_pages: Sequence[Path],
        audio_dir: Path,
        is_active: bool,
        active_generation: Optional[str],
    ) -> _PageSnapshot:
        pages: list[dict[str, object]] = []
        ready_ids: set[str] = set()
        total_audio_sec = 0.0
        latest_ready_id: Optional[str] = None

        for page in all_pages:
            page_id = page.stem
            wav_file = audio_dir / f"{page_id}.wav"
            txt_file = audio_dir / f"{page_id}_normalized.txt"
            has_wav = self._page_repo.audio_exists(wav_file, min_bytes=1000)
            has_txt = self._page_repo.page_exists(txt_file, min_bytes=1)
            duration = self._stitcher.get_file_duration_sec(wav_file) if has_wav else 0.0

            if has_wav:
                ready_ids.add(page_id)
                latest_ready_id = page_id
                total_audio_sec += duration

            status = "ready"
            if not has_wav:
                status = "generating" if is_active and page_id == active_generation else "pending"

            raw_markdown = self._read_page(page)
            title = extract_markdown_title(
                raw_markdown,
                fallback_title=page_id.replace("_", " ").title(),
            )
            pages.append(
                {
                    "id": page_id,
                    "filename": page.name,
                    "title": title,
                    "status": status,
                    "has_wav": has_wav,
                    "has_txt": has_txt,
                    "duration": round(duration, 2),
                    "duration_str": self._format_duration(duration) if has_wav else "--:--",
                }
            )

        return _PageSnapshot(pages, ready_ids, total_audio_sec, latest_ready_id)

    def _build_active_page(
        self,
        all_pages: Sequence[Path],
        audio_dir: Path,
        active_generation: str,
        state_data: dict[str, object],
    ) -> dict[str, object]:
        normalized_path = audio_dir / f"{active_generation}_normalized.txt"
        segment_count = self._count_segments(normalized_path)
        active_title = active_generation
        page_map = {page.stem: page for page in all_pages}
        active_file = page_map.get(active_generation)
        if active_file is not None:
            active_title = extract_markdown_title(
                self._read_page(active_file),
                fallback_title=active_generation,
            )

        stage_details = self._build_stage_details(state_data, active_generation)
        page_suffix = active_generation.replace("page_", "")
        page_number = int(page_suffix) if page_suffix.isdigit() else 0
        return {
            "id": active_generation,
            "title": active_title,
            "page_num": page_number,
            "total_segments": stage_details.get("total_segments", segment_count) if stage_details else segment_count,
            "current_segment": stage_details.get("current_segment", 1) if stage_details else 1,
            "completed_segments": stage_details.get("completed_segments", 0) if stage_details else 0,
            "segment_percent": stage_details.get("segment_percent", 0.0) if stage_details else 0.0,
            "current_sentence": (
                stage_details.get("current_sentence", "Trwa przetwarzanie tekstu...")
                if stage_details
                else "Trwa przetwarzanie tekstu..."
            ),
            "stage_description": (
                stage_details.get("stage_description", "Generowanie segmentów strony...")
                if stage_details
                else "Generowanie segmentów strony..."
            ),
        }

    def _build_stage_details(
        self,
        state_data: dict[str, object],
        active_generation: str,
    ) -> Optional[dict[str, object]]:
        timestamp = _safe_float(state_data.get("timestamp"))
        if state_data.get("page_id") != active_generation or time.time() - timestamp >= 180:
            return None

        completed = _safe_int(state_data.get("completed_segments"))
        total = _safe_int(state_data.get("total_segments"), 1)
        current_from_state = _safe_int(state_data.get("current_segment"))
        current_segment = current_from_state if current_from_state > 0 else min(total, completed + 1)
        percentage = _safe_float(state_data.get("segment_percent") or state_data.get("percentage"))
        sentence = str(
            state_data.get("current_sentence") or state_data.get("current_segment_text") or "Trwa synteza segmentu..."
        )
        description = str(
            state_data.get("stage_description") or f"Synteza mowy: segment {current_segment} z {total} ({percentage}%)"
        )
        return {
            "current_segment": current_segment,
            "total_segments": total,
            "completed_segments": completed,
            "segment_percent": round(percentage, 1),
            "current_sentence": sentence,
            "stage_description": description,
        }

    def _count_segments(self, path: Path) -> int:
        if not self._page_repo.page_exists(path):
            return 0
        return len([line for line in self._read_page(path).splitlines() if line.strip()])

    def _read_page(self, path: Path) -> str:
        try:
            return self._page_repo.read_markdown(path)
        except (OSError, UnicodeError):
            return ""

    def _build_progress(
        self,
        all_pages: Sequence[Path],
        snapshot: _PageSnapshot,
        processing_state: _ProcessingState,
        is_active: bool,
        active_page: Optional[dict[str, object]],
    ) -> dict[str, object]:
        remaining_count = max(0, len(all_pages) - len(snapshot.ready_ids))
        average_page_sec = snapshot.total_audio_sec / len(snapshot.ready_ids) * 1.15 if snapshot.ready_ids else 70.0
        eta_sec = remaining_count * average_page_sec
        eta_hours = int(eta_sec // 3600)
        eta_minutes = int((eta_sec % 3600) // 60)
        eta_str = f"{eta_hours}h {eta_minutes}m" if eta_hours > 0 else f"{eta_minutes} min"

        total_hours = int(snapshot.total_audio_sec // 3600)
        total_minutes = int((snapshot.total_audio_sec % 3600) // 60)
        total_seconds = int(snapshot.total_audio_sec % 60)
        total_audio_str = (
            f"{total_hours}h {total_minutes}m {total_seconds}s"
            if total_hours > 0
            else f"{total_minutes}m {total_seconds}s"
        )
        percentage = round(len(snapshot.ready_ids) / len(all_pages) * 100.0, 1) if all_pages else 0.0
        state_data = processing_state.data
        return {
            "ready_count": len(snapshot.ready_ids),
            "total_count": len(all_pages),
            "percent": percentage,
            "is_active": is_active,
            "active_page": active_page,
            "eta_str": eta_str if is_active else "Zakończono / Bezczynny",
            "total_audio_sec": round(snapshot.total_audio_sec, 1),
            "total_audio_str": total_audio_str,
            "last_page_duration_sec": _safe_float(state_data.get("last_page_duration_sec")),
            "average_page_duration_sec": _safe_float(state_data.get("average_page_duration_sec")),
            "vram_used_mb": _safe_float(state_data.get("vram_used_mb")),
            "vram_total_mb": _safe_float(state_data.get("vram_total_mb")),
            "gpu_utilization_pct": _safe_float(state_data.get("gpu_utilization_pct")),
        }

    @staticmethod
    def _format_duration(duration: float) -> str:
        return f"{int(duration // 60):02d}:{int(duration % 60):02d}"
