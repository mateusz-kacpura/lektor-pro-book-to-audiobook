"""
lektor.infrastructure.container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Central Composition Root and IoC container for the Lektor application.
Initializes repositories, engines, adapters, and use cases.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..adapters.gui.job_manager import JobExecutionManager
    from ..adapters.gui.paths import GuiPaths

from ..adapters.audio.cleaner import SileroAudioCleaner
from ..adapters.audio.stitcher import NumpyAudioStitcher
from ..adapters.audio.voice_scanner import FileSystemVoiceDiscoveryAdapter
from ..adapters.ocr.formatter import DefaultBookMarkdownFormatter
from ..adapters.ocr.pdf_splitter import PyMuPdfSplitterAdapter
from ..adapters.ocr.vision_adapter import UniversalVisionTranslatorAdapter
from ..adapters.storage.book_repository import FileSystemBookRepository
from ..adapters.storage.file_repository import FileSystemPageRepository
from ..adapters.storage.notes_repository import FileSystemNotesRepository
from ..adapters.storage.studio_repository import FileSystemStudioHistoryRepository
from ..adapters.tts.cache import AudioSegmentCache
from ..adapters.tts.factory import TTSEngineFactory
from ..application.ports.audio_ports import (
    AudioCacheProtocol,
    AudioCleanerProtocol,
    AudioStitcherProtocol,
    TTSEngineProtocol,
    VoiceDiscoveryProtocol,
)
from ..application.ports.ocr_ports import (
    PdfSplitterProtocol,
    VisionTranslatorProtocol,
)
from ..application.ports.resource_ports import AIModelArbiterProtocol
from ..application.ports.storage_ports import (
    BookRepositoryProtocol,
    NotesRepositoryProtocol,
    PageRepositoryProtocol,
    StudioHistoryRepositoryProtocol,
)
from ..application.ports.telemetry_ports import (
    GpuTelemetryProtocol,
    ProgressReporterProtocol,
    TelemetryBroadcasterProtocol,
)
from ..application.use_cases.batch_synthesis import BatchSynthesisUseCase
from ..application.use_cases.convert_book import ConvertBookUseCase
from ..application.use_cases.convert_pdf_book import ConvertPdfBookUseCase
from ..application.use_cases.get_book_status import GetBookStatusUseCase
from ..application.use_cases.import_pdf_book import ImportPdfBookUseCase
from ..application.use_cases.list_books import ListBooksUseCase
from ..application.use_cases.preview_page import PreviewPageUseCase
from ..application.use_cases.render_pdf_scans import RenderPdfScansUseCase
from ..application.use_cases.render_scans_stream import RenderPdfScansStreamUseCase
from ..application.use_cases.switch_active_book import SwitchActiveBookUseCase
from ..application.use_cases.synthesize_page import SynthesizePageUseCase
from ..application.use_cases.synthesize_snippet import SynthesizeMarkdownSnippetUseCase
from ..domain.audio_models import CodeMode, SynthesisConfig
from ..domain.normalization import TextNormalizationService
from .config import DataPaths, settings


class ApplicationContainer:
    """
    Central Composition Root for the application (CLI and Web GUI).
    Encapsulates the creation and lifecycle of domain services and adapters.
    """

    def __init__(
        self,
        data_paths: Optional[DataPaths] = None,
        base_dir: Optional[Path] = None,
    ) -> None:
        self._data_paths: DataPaths = data_paths or DataPaths.from_data_dir()
        self._base_dir: Path = (base_dir or settings.base_dir).resolve()

        self._job_manager: Optional[JobExecutionManager] = None
        self._book_repo: Optional[BookRepositoryProtocol] = None
        self._notes_repo: Optional[NotesRepositoryProtocol] = None
        self._studio_repo: Optional[StudioHistoryRepositoryProtocol] = None
        self._page_repo: Optional[PageRepositoryProtocol] = None
        self._tts_engine: Optional[TTSEngineProtocol] = None
        self._audio_stitcher: Optional[AudioStitcherProtocol] = None
        self._audio_cache: Optional[AudioCacheProtocol] = None
        self._audio_cleaner: Optional[AudioCleanerProtocol] = None
        self._normalization_service: Optional[TextNormalizationService] = None
        self._model_arbiter: Optional[AIModelArbiterProtocol] = None
        self._pdf_splitter: Optional[PdfSplitterProtocol] = None
        self._vision_translator: Optional[VisionTranslatorProtocol] = None
        self._telemetry_broadcaster: Optional[TelemetryBroadcasterProtocol] = None
        self._gpu_telemetry: Optional[GpuTelemetryProtocol] = None
        self._voice_discovery: Optional[VoiceDiscoveryProtocol] = None

        try:
            from ..adapters.text.spelling import PolishNumberSpellingAdapter
            from ..domain.normalizers.numbers import set_default_speller

            set_default_speller(PolishNumberSpellingAdapter())
        except ImportError:
            pass

    def get_job_manager(self) -> "JobExecutionManager":
        """Returns the instance of the GUI job execution manager."""
        if self._job_manager is None:
            from ..adapters.gui.job_manager import JobExecutionManager

            self._job_manager = JobExecutionManager()
        return self._job_manager

    @property
    def data_paths(self) -> DataPaths:
        return self._data_paths

    def shutdown(self) -> None:
        """Releases models managed by the application, including those from previous sessions."""
        arbiter = self._model_arbiter or self.get_model_arbiter()
        arbiter.release_all()

    def reset_book_context(self, new_paths: Optional[object] = None) -> None:
        """
        Invalidates instances bound to a specific book's state
        after switching the active book slug.
        """
        if isinstance(new_paths, DataPaths):
            self._data_paths = new_paths
        else:
            self._data_paths = DataPaths.from_data_dir()
        self._book_repo = None
        self._page_repo = None
        self._audio_cache = None
        self._notes_repo = None

    def get_data_paths(self) -> DataPaths:
        return self._data_paths

    def get_gui_paths(self) -> "GuiPaths":
        from ..adapters.gui.paths import create_gui_paths

        return create_gui_paths(base_dir=self._base_dir, data_paths=self._data_paths)

    def get_book_repository(self) -> BookRepositoryProtocol:
        if self._book_repo is None:
            self._book_repo = FileSystemBookRepository(
                books_dir=self._data_paths.books_dir,
                default_active_slug=self._data_paths.active_book_slug,
            )
        return self._book_repo

    def get_notes_repository(self) -> NotesRepositoryProtocol:
        if self._notes_repo is None:
            self._notes_repo = FileSystemNotesRepository(notes_dir=self._data_paths.notes_dir)
        return self._notes_repo

    def get_studio_history_repository(self) -> StudioHistoryRepositoryProtocol:
        if self._studio_repo is None:
            self._studio_repo = FileSystemStudioHistoryRepository(
                history_file=self._data_paths.studio_history_file,
                audio_dir=self._data_paths.studio_audio_dir,
            )
        return self._studio_repo

    def get_page_repository(self) -> PageRepositoryProtocol:
        if self._page_repo is None:
            self._page_repo = FileSystemPageRepository()
        return self._page_repo

    def get_tts_engine(self) -> TTSEngineProtocol:
        if self._tts_engine is None:
            cfg = SynthesisConfig(
                temperature=0.33,
                cfg_weight=0.68,
                exaggeration=0.25,
                reference_voice_path=self._data_paths.default_voice_path if self._data_paths.default_voice_path.exists() else None,
            )
            self._tts_engine = TTSEngineFactory.create(
                engine_type=settings.tts_engine,
                model_name_or_path=settings.omnivoice_model_id,
                reference_voice_path=cfg.reference_voice_path,
                config=cfg,
                cleaner=self.get_audio_cleaner(),
                cache=self.get_audio_cache(),
            )
        return self._tts_engine

    def get_audio_stitcher(self) -> AudioStitcherProtocol:
        if self._audio_stitcher is None:
            self._audio_stitcher = NumpyAudioStitcher(sample_rate=24000)
        return self._audio_stitcher

    def get_audio_cleaner(self) -> AudioCleanerProtocol:
        if self._audio_cleaner is None:
            self._audio_cleaner = SileroAudioCleaner(sample_rate=24000)
        return self._audio_cleaner

    def get_audio_cache(self) -> AudioCacheProtocol:
        if self._audio_cache is None:
            cache_dir = self._data_paths.audio_dir / ".cache" / "segments"
            self._audio_cache = AudioSegmentCache(cache_dir=cache_dir)
        return self._audio_cache

    def get_normalization_service(self, code_mode: CodeMode = "spoken") -> TextNormalizationService:
        if self._normalization_service is None or self._normalization_service.code_mode != code_mode:
            self._normalization_service = TextNormalizationService(code_mode=code_mode)
        return self._normalization_service

    def get_pdf_splitter(self) -> PdfSplitterProtocol:
        if self._pdf_splitter is None:
            self._pdf_splitter = PyMuPdfSplitterAdapter()
        return self._pdf_splitter

    def get_vision_translator(self, model_name: Optional[str] = None) -> VisionTranslatorProtocol:
        target_model = model_name or "google/gemma-4-12b"
        if model_name:
            return UniversalVisionTranslatorAdapter(model_name=target_model)
        if self._vision_translator is None:
            self._vision_translator = UniversalVisionTranslatorAdapter(model_name=target_model)
        return self._vision_translator

    def get_telemetry_broadcaster(self) -> TelemetryBroadcasterProtocol:
        if self._telemetry_broadcaster is None:
            from ..adapters.gui.broadcaster import SseTelemetryBroadcasterAdapter

            self._telemetry_broadcaster = SseTelemetryBroadcasterAdapter()
        return self._telemetry_broadcaster

    def get_gpu_telemetry(self) -> GpuTelemetryProtocol:
        if self._gpu_telemetry is None:
            from ..adapters.gui.gpu_adapter import NvidiaSmiGpuTelemetryAdapter

            self._gpu_telemetry = NvidiaSmiGpuTelemetryAdapter()
        return self._gpu_telemetry

    def get_voice_discovery(self) -> VoiceDiscoveryProtocol:
        if self._voice_discovery is None:
            self._voice_discovery = FileSystemVoiceDiscoveryAdapter(
                data_dir=self._data_paths.data_dir,
                default_voice=self._data_paths.default_voice_path,
            )
        return self._voice_discovery

    def get_model_arbiter(self) -> AIModelArbiterProtocol:
        if self._model_arbiter is None:
            from ..adapters.resources.arbiter import (
                DynamicVramModelArbiter,
                ProcessModelHandle,
                PyTorchModelHandle,
            )
            from ..domain.resource_models import (
                SLOT_AUDIO_TTS,
                SLOT_VISION,
                ModelResourceId,
            )

            tts_handle = PyTorchModelHandle(
                slot_id=SLOT_AUDIO_TTS,
                resource_id=ModelResourceId(settings.omnivoice_model_id),
                engine=self.get_tts_engine(),
            )

            server_args = [
                "-m",
                str(settings.llama_model_path),
                "--mmproj",
                str(settings.llama_mmproj_path),
                "--host",
                "0.0.0.0",
                "--port",
                str(settings.llama_server_port),
                "-ngl",
                "99",
                "-ub",
                "2048",
                "--reasoning-budget",
                "0",
                "--alias",
                "google/gemma-4-12b",
                "-c",
                "8192",
            ]
            vision_handle = ProcessModelHandle(
                slot_id=SLOT_VISION,
                resource_id=ModelResourceId("google/gemma-4-12b"),
                executable_path=settings.llama_server_binary,
                args=server_args,
                health_check_url=f"http://127.0.0.1:{settings.llama_server_port}/v1/models",
                process_name_for_kill="llama-server.exe",
            )

            self._model_arbiter = DynamicVramModelArbiter(handles=[vision_handle, tts_handle])
        return self._model_arbiter

    # --- Use Cases Factory Methods ---

    def create_preview_page_use_case(self, code_mode: CodeMode = "spoken") -> PreviewPageUseCase:
        return PreviewPageUseCase(
            page_repository=self.get_page_repository(),
            normalization_service=self.get_normalization_service(code_mode=code_mode),
        )

    def create_synthesize_snippet_use_case(self) -> SynthesizeMarkdownSnippetUseCase:
        return SynthesizeMarkdownSnippetUseCase(
            tts_engine=self.get_tts_engine(),
            audio_stitcher=self.get_audio_stitcher(),
            normalization_service=self.get_normalization_service(),
            audio_cache=self.get_audio_cache(),
            model_arbiter=self.get_model_arbiter(),
        )

    def create_synthesize_page_use_case(
        self,
        tts_engine: Optional[TTSEngineProtocol] = None,
        model_arbiter: Optional[AIModelArbiterProtocol] = None,
    ) -> SynthesizePageUseCase:
        arbiter = model_arbiter if model_arbiter is not None else (None if tts_engine is not None else self.get_model_arbiter())
        return SynthesizePageUseCase(
            tts_engine=tts_engine or self.get_tts_engine(),
            audio_stitcher=self.get_audio_stitcher(),
            page_repository=self.get_page_repository(),
            normalization_service=self.get_normalization_service(),
            model_arbiter=arbiter,
        )

    def create_batch_synthesis_use_case(
        self,
        synthesize_page_uc: Optional[SynthesizePageUseCase] = None,
        progress_reporter: Optional[ProgressReporterProtocol] = None,
    ) -> BatchSynthesisUseCase:
        return BatchSynthesisUseCase(
            synthesize_page_uc=synthesize_page_uc or self.create_synthesize_page_use_case(),
            page_repository=self.get_page_repository(),
            progress_reporter=progress_reporter,
        )

    def create_convert_book_use_case(
        self,
        progress_reporter: Optional[ProgressReporterProtocol] = None,
        vision_translator: Optional[VisionTranslatorProtocol] = None,
    ) -> ConvertBookUseCase:
        return ConvertBookUseCase(
            vision_translator=vision_translator or self.get_vision_translator(),
            markdown_formatter=DefaultBookMarkdownFormatter(),
            page_repository=self.get_page_repository(),
            progress_reporter=progress_reporter,
        )

    def create_list_books_use_case(self) -> ListBooksUseCase:
        return ListBooksUseCase(book_repo=self.get_book_repository())

    def create_switch_active_book_use_case(self) -> SwitchActiveBookUseCase:
        return SwitchActiveBookUseCase(book_repo=self.get_book_repository())

    def create_import_pdf_book_use_case(self) -> ImportPdfBookUseCase:
        return ImportPdfBookUseCase(
            book_repository=self.get_book_repository(),
            pdf_splitter=self.get_pdf_splitter(),
        )

    def create_convert_pdf_book_use_case(self, model_name: Optional[str] = None) -> ConvertPdfBookUseCase:
        return ConvertPdfBookUseCase(
            pdf_splitter=self.get_pdf_splitter(),
            vision_translator=self.get_vision_translator(model_name=model_name),
            page_repository=self.get_page_repository(),
            broadcaster=self.get_telemetry_broadcaster(),
            gpu_telemetry=self.get_gpu_telemetry(),
            book_repository=self.get_book_repository(),
            model_arbiter=self.get_model_arbiter(),
        )

    def create_render_scans_stream_use_case(self) -> RenderPdfScansStreamUseCase:
        return RenderPdfScansStreamUseCase(
            book_repository=self.get_book_repository(),
            pdf_splitter=self.get_pdf_splitter(),
        )

    def create_render_pdf_scans_use_case(self) -> RenderPdfScansUseCase:
        return RenderPdfScansUseCase(
            book_repository=self.get_book_repository(),
            pdf_splitter=self.get_pdf_splitter(),
        )

    def create_get_book_status_use_case(self) -> GetBookStatusUseCase:
        return GetBookStatusUseCase(
            book_repository=self.get_book_repository(),
            page_repository=self.get_page_repository(),
            audio_stitcher=self.get_audio_stitcher(),
            voice_discovery=self.get_voice_discovery(),
            job_status_provider=self.get_job_manager(),
        )


# Implementation note: see the surrounding code for the behavior described here.
default_container = ApplicationContainer()
