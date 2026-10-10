"""
lektor.adapters.gui.dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~
FastAPI dependency providers injecting container services into endpoints.
"""

from typing import cast

from fastapi import Depends, HTTPException, Request

from ...application.ports.audio_ports import (
    AudioCacheProtocol,
    AudioStitcherProtocol,
    TTSEngineProtocol,
    VoiceDiscoveryProtocol,
)
from ...application.ports.container_ports import ApplicationContainerProtocol
from ...application.ports.ocr_ports import (
    PdfSplitterProtocol,
    VisionTranslatorProtocol,
)
from ...application.ports.resource_ports import AIModelArbiterProtocol
from ...application.ports.storage_ports import (
    BookRepositoryProtocol,
    NotesRepositoryProtocol,
    PageRepositoryProtocol,
    StudioHistoryRepositoryProtocol,
)
from ...application.ports.telemetry_ports import (
    GpuTelemetryProtocol,
    TelemetryBroadcasterProtocol,
)
from ...application.use_cases.batch_synthesis import BatchSynthesisUseCase
from ...application.use_cases.convert_pdf_book import ConvertPdfBookUseCase
from ...application.use_cases.get_book_status import GetBookStatusUseCase
from ...application.use_cases.import_pdf_book import ImportPdfBookUseCase
from ...application.use_cases.list_books import ListBooksUseCase
from ...application.use_cases.preview_page import PreviewPageUseCase
from ...application.use_cases.render_pdf_scans import RenderPdfScansUseCase
from ...application.use_cases.render_scans_stream import RenderPdfScansStreamUseCase
from ...application.use_cases.switch_active_book import SwitchActiveBookUseCase
from ...application.use_cases.synthesize_page import SynthesizePageUseCase
from ...application.use_cases.synthesize_snippet import SynthesizeMarkdownSnippetUseCase
from ...domain.normalization import TextNormalizationService
from .job_manager import JobExecutionManager
from .paths import GuiPaths


def get_container(request: Request) -> ApplicationContainerProtocol:
    """Container provider retrieved directly from application state."""
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise HTTPException(status_code=500, detail="Kontener aplikacji nie został zainicjalizowany w app.state")
    return cast(ApplicationContainerProtocol, container)


def get_gui_paths(request: Request) -> GuiPaths:
    """Web GUI path configuration provider retrieved from application state."""
    paths = getattr(request.app.state, "gui_paths", None)
    if paths is None:
        raise HTTPException(status_code=500, detail="Konfiguracja GuiPaths nie została zarejestrowana w app.state")
    return cast(GuiPaths, paths)


def get_job_manager(container: ApplicationContainerProtocol = Depends(get_container)) -> JobExecutionManager:
    return cast(JobExecutionManager, container.get_job_manager())


def get_book_repository(container: ApplicationContainerProtocol = Depends(get_container)) -> BookRepositoryProtocol:
    return container.get_book_repository()


def get_notes_repository(container: ApplicationContainerProtocol = Depends(get_container)) -> NotesRepositoryProtocol:
    return container.get_notes_repository()


def get_studio_history_repository(container: ApplicationContainerProtocol = Depends(get_container)) -> StudioHistoryRepositoryProtocol:
    return container.get_studio_history_repository()


def get_page_repository(container: ApplicationContainerProtocol = Depends(get_container)) -> PageRepositoryProtocol:
    return container.get_page_repository()


def get_tts_engine(container: ApplicationContainerProtocol = Depends(get_container)) -> TTSEngineProtocol:
    return container.get_tts_engine()


def get_audio_stitcher(container: ApplicationContainerProtocol = Depends(get_container)) -> AudioStitcherProtocol:
    return container.get_audio_stitcher()


def get_audio_cache(container: ApplicationContainerProtocol = Depends(get_container)) -> AudioCacheProtocol:
    return container.get_audio_cache()


def get_normalization_service(container: ApplicationContainerProtocol = Depends(get_container)) -> TextNormalizationService:
    return container.get_normalization_service()


def get_pdf_splitter(container: ApplicationContainerProtocol = Depends(get_container)) -> PdfSplitterProtocol:
    return container.get_pdf_splitter()


def get_vision_translator(container: ApplicationContainerProtocol = Depends(get_container)) -> VisionTranslatorProtocol:
    return container.get_vision_translator()


def get_telemetry_broadcaster(container: ApplicationContainerProtocol = Depends(get_container)) -> TelemetryBroadcasterProtocol:
    return container.get_telemetry_broadcaster()


def get_gpu_telemetry(container: ApplicationContainerProtocol = Depends(get_container)) -> GpuTelemetryProtocol:
    return container.get_gpu_telemetry()


def get_model_arbiter(container: ApplicationContainerProtocol = Depends(get_container)) -> AIModelArbiterProtocol:
    return container.get_model_arbiter()


def get_preview_page_use_case(container: ApplicationContainerProtocol = Depends(get_container)) -> PreviewPageUseCase:
    return container.create_preview_page_use_case()


def get_synthesize_snippet_use_case(container: ApplicationContainerProtocol = Depends(get_container)) -> SynthesizeMarkdownSnippetUseCase:
    return container.create_synthesize_snippet_use_case()


def get_synthesize_page_use_case(container: ApplicationContainerProtocol = Depends(get_container)) -> SynthesizePageUseCase:
    return container.create_synthesize_page_use_case()


def get_batch_synthesis_use_case(container: ApplicationContainerProtocol = Depends(get_container)) -> BatchSynthesisUseCase:
    return container.create_batch_synthesis_use_case()


def get_list_books_use_case(container: ApplicationContainerProtocol = Depends(get_container)) -> ListBooksUseCase:
    return container.create_list_books_use_case()


def get_switch_active_book_use_case(container: ApplicationContainerProtocol = Depends(get_container)) -> SwitchActiveBookUseCase:
    return container.create_switch_active_book_use_case()


def get_import_pdf_book_use_case(container: ApplicationContainerProtocol = Depends(get_container)) -> ImportPdfBookUseCase:
    return container.create_import_pdf_book_use_case()


def get_convert_pdf_book_use_case(container: ApplicationContainerProtocol = Depends(get_container)) -> ConvertPdfBookUseCase:
    return container.create_convert_pdf_book_use_case()


def get_render_scans_stream_use_case(container: ApplicationContainerProtocol = Depends(get_container)) -> RenderPdfScansStreamUseCase:
    return container.create_render_scans_stream_use_case()


def get_render_pdf_scans_use_case(container: ApplicationContainerProtocol = Depends(get_container)) -> RenderPdfScansUseCase:
    return container.create_render_pdf_scans_use_case()


def get_voice_discovery(container: ApplicationContainerProtocol = Depends(get_container)) -> VoiceDiscoveryProtocol:
    return container.get_voice_discovery()


def get_book_status_use_case(container: ApplicationContainerProtocol = Depends(get_container)) -> GetBookStatusUseCase:
    return container.create_get_book_status_use_case()