"""
lektor.infrastructure.config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Environment and hardware configuration (GPU/CPU) and centralized data path management.
Frameworks & Drivers layer. Serves as the Single Source of Truth (SSOT)
for all adapters, repositories, and helper modules.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from ..domain.book_models import DataPaths as DomainDataPaths

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


def load_env_file(dotenv_path: Path | None = None) -> None:
    """
    Loads environment variables from a .env file without external dependencies.
    Does not overwrite variables that already exist in the process environment.
    """
    target = dotenv_path or (PROJECT_ROOT / ".env")
    if not target.exists() or not target.is_file():
        return
    try:
        content = target.read_text(encoding="utf-8")
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                key, val = stripped.split("=", 1)
                k = key.strip()
                v = val.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


# Implementation note: see the surrounding code for the behavior described here.
load_env_file()


def resolve_device(preferred_device: str = "auto") -> str:
    """Automatically detects and selects the best computing device."""
    if preferred_device != "auto":
        return preferred_device
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


def resolve_default_data_dir() -> Path:
    """
    Resolves the default data directory path (SSOT).
    Priority:
    1. LEKTOR_DATA_DIR environment variable
    2. PROJECT_ROOT / 'data'
    """
    env_dir = os.environ.get("LEKTOR_DATA_DIR")
    if env_dir:
        return Path(env_dir).resolve()
    candidate = PROJECT_ROOT / "data"
    if candidate.exists():
        return candidate.resolve()
    return PROJECT_ROOT.resolve()


@dataclass(frozen=True)
class DataPaths(DomainDataPaths):
    """
    Infrastructure implementation of data path configuration.
    Extends the domain model DataPaths with physical directory creation.
    """

    @classmethod
    def from_data_dir(
        cls,
        custom_data_dir: Path | str | None = None,
        active_book: str | None = None,
    ) -> "DataPaths":
        """
        Creates a DataPaths instance based on the specified data directory
        and active book slug.
        """
        base = Path(custom_data_dir).resolve() if custom_data_dir is not None else resolve_default_data_dir()
        books = base / "books"
        voice = base / "audio.wav"

        active_marker = books / ".active"
        active_from_file: str | None = None
        if active_marker.exists():
            try:
                content = active_marker.read_text(encoding="utf-8").strip()
                if content:
                    active_from_file = content
            except Exception:
                pass

        slug = active_book or active_from_file or os.environ.get("LEKTOR_ACTIVE_BOOK", "cloud_native_go")
        active_book_dir = books / slug

        # Markdown pages
        if (active_book_dir / "pages").exists():
            pages = active_book_dir / "pages"
        elif (base / "pages").exists():
            pages = base / "pages"
        else:
            pages = active_book_dir / "pages"

        # Implementation note: see the surrounding code for the behavior described here.
        if active_book_dir.exists():
            audio = active_book_dir / "audio"
        elif (base / "audio_book").exists():
            audio = base / "audio_book"
        else:
            audio = active_book_dir / "audio"

        # Scans and images
        scans = active_book_dir / "scans" if (active_book_dir / "scans").exists() else base / "pdf_pages_jpg"
        images = active_book_dir / "images" if (active_book_dir / "images").exists() else base / "images"

        # Implementation note: see the surrounding code for the behavior described here.
        app_audio = base / "audio_book"
        studio = app_audio / "studio"
        return cls(
            data_dir=base,
            books_dir=books,
            audio_dir=audio,
            pages_dir=pages,
            scans_dir=scans,
            notes_dir=base / "notes",
            cache_dir=app_audio / ".cache" / "segments",
            default_voice_path=voice,
            images_dir=images,
            studio_audio_dir=studio,
            studio_history_file=studio / "history.json",
            active_book_slug=slug,
        )


@dataclass
class InfrastructureSettings:
    """Application infrastructure settings."""
    device: str = field(default_factory=lambda: resolve_device(os.environ.get("LEKTOR_DEVICE", "auto")))
    base_dir: Path = field(default_factory=lambda: PROJECT_ROOT)
    data_paths: DataPaths = field(default_factory=DataPaths.from_data_dir)
    gui_host: str = field(default_factory=lambda: os.environ.get("LEKTOR_GUI_HOST", "127.0.0.1"))
    gui_port: int = field(default_factory=lambda: int(os.environ.get("LEKTOR_GUI_PORT", "7860")))
    auto_open_browser: bool = field(
        default_factory=lambda: os.environ.get("LEKTOR_AUTO_OPEN_BROWSER", "true").lower() in ("true", "1", "yes")
    )
    tts_engine: str = field(
        default_factory=lambda: os.environ.get("LEKTOR_TTS_ENGINE", "omnivoice")
    )
    omnivoice_model_id: str = field(
        default_factory=lambda: os.environ.get("LEKTOR_OMNIVOICE_MODEL", os.environ.get("LEKTOR_TTS_MODEL", "k2-fsa/OmniVoice"))
    )
    chatterbox_model_id: str = field(
        default_factory=lambda: os.environ.get("LEKTOR_CHATTERBOX_MODEL", "ResembleAI/chatterbox")
    )
    vision_model_id: str = field(
        default_factory=lambda: os.environ.get("LEKTOR_VISION_MODEL", "google/gemma-4-12b")
    )
    vision_api_url: str = field(
        default_factory=lambda: os.environ.get("LEKTOR_VISION_API_URL", "http://127.0.0.1:1234/v1")
    )
    llama_server_binary: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "LEKTOR_LLAMA_SERVER_BINARY",
                str(
                    Path.home()
                    / ".lmstudio"
                    / "extensions"
                    / "backends"
                    / "llama.cpp-win-x86_64-nvidia-cuda12-avx2-2.53.0"
                    / "llama-server.exe"
                ),
            )
        )
    )
    llama_model_path: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "LEKTOR_LLAMA_MODEL_PATH",
                str(
                    Path.home()
                    / ".lmstudio"
                    / "models"
                    / "lmstudio-community"
                    / "gemma-4-12B-it-GGUF"
                    / "gemma-4-12B-it-Q4_K_M.gguf"
                ),
            )
        )
    )
    llama_mmproj_path: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "LEKTOR_LLAMA_MMPROJ_PATH",
                str(
                    Path.home()
                    / ".lmstudio"
                    / "models"
                    / "lmstudio-community"
                    / "gemma-4-12B-it-GGUF"
                    / "mmproj-gemma-4-12B-it-BF16.gguf"
                ),
            )
        )
    )
    llama_server_port: int = field(
        default_factory=lambda: int(os.environ.get("LEKTOR_LLAMA_SERVER_PORT", "1234"))
    )

    @property
    def data_dir(self) -> Path:
        return self.data_paths.data_dir

    @property
    def books_dir(self) -> Path:
        return self.data_paths.books_dir

    @property
    def audio_dir(self) -> Path:
        return self.data_paths.audio_dir

    @property
    def pages_dir(self) -> Path:
        return self.data_paths.pages_dir

    @property
    def notes_dir(self) -> Path:
        return self.data_paths.notes_dir

    @property
    def default_voice_path(self) -> Path:
        return self.data_paths.default_voice_path


settings = InfrastructureSettings()

