"""
lektor.adapters.gui.paths
~~~~~~~~~~~~~~~~~~~~~~~~~
Filesystem path configuration for the Web GUI adapter.
"""

from dataclasses import dataclass
from pathlib import Path

from ...domain.book_models import DataPaths


@dataclass(frozen=True)
class GuiPaths:
    base_dir: Path
    gui_dir: Path
    static_dir: Path
    templates_dir: Path
    data_dir: Path
    books_dir: Path
    pages_dir: Path
    audio_dir: Path
    notes_dir: Path
    default_voice: Path
    images_dir: Path
    pdf_pages_dir: Path
    studio_audio_dir: Path
    studio_history_file: Path


def create_gui_paths(
    base_dir: Path,
    data_paths: DataPaths,
) -> GuiPaths:
    b_dir = base_dir.resolve()
    gui_adapter_dir = b_dir / "lektor" / "adapters" / "gui"
    gui_legacy_dir = b_dir / "lektor" / "gui"
    g_dir = gui_adapter_dir if (gui_adapter_dir / "templates").exists() else gui_legacy_dir
    s_dir = g_dir / "static"
    s_dir.mkdir(parents=True, exist_ok=True)
    t_dir = g_dir / "templates"

    a_dir = data_paths.audio_dir
    a_dir.mkdir(parents=True, exist_ok=True)

    n_dir = data_paths.notes_dir
    n_dir.mkdir(parents=True, exist_ok=True)

    st_audio = data_paths.studio_audio_dir
    st_audio.mkdir(parents=True, exist_ok=True)

    return GuiPaths(
        base_dir=b_dir,
        gui_dir=g_dir,
        static_dir=s_dir,
        templates_dir=t_dir,
        data_dir=data_paths.data_dir,
        books_dir=data_paths.books_dir,
        pages_dir=data_paths.pages_dir,
        audio_dir=a_dir,
        notes_dir=n_dir,
        default_voice=data_paths.default_voice_path,
        images_dir=data_paths.images_dir,
        pdf_pages_dir=data_paths.scans_dir,
        studio_audio_dir=st_audio,
        studio_history_file=data_paths.studio_history_file,
    )