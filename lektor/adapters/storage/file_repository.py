"""Filesystem page repository managing Markdown and audio files."""

import json
import re
from pathlib import Path
from typing import Sequence

from ...application.ports.storage_ports import PageRepositoryProtocol
from ...domain.audio_models import SynthesisStats


class FileSystemPageRepository(PageRepositoryProtocol):
    """Repository implementing PageRepositoryProtocol."""

    def read_markdown(self, path: Path) -> str:
        """Reads Markdown file content in UTF-8 encoding."""
        return path.read_text(encoding="utf-8")

    def write_markdown(self, path: Path, content: str) -> None:
        """Writes content to Markdown file, creating parent directories if needed."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def list_pages(self, directory: Path, pattern: str = "*.md") -> Sequence[Path]:
        """
        Wyszukuje pliki stron Markdown i sortuje je numerycznie wg numeru strony.
        """
        if not directory.exists():
            return []

        all_files = list(directory.glob(pattern))

        def sort_key(p: Path) -> tuple[int, str]:
            match = re.search(r"\d+", p.stem)
            if match:
                return (int(match.group()), p.name)
            return (999999, p.name)

        return sorted(all_files, key=sort_key)

    def save_preview(self, path: Path, text: str) -> None:
        """Saves normalized text preview file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def page_exists(self, path: Path, min_bytes: int = 0) -> bool:
        """Sprawdza, czy plik strony Markdown istnieje i ma wymagany rozmiar."""
        if not path.exists():
            return False
        try:
            return path.stat().st_size >= min_bytes
        except OSError:
            return False

    def get_page_size(self, path: Path) -> int:
        """Returns page file size in bytes."""
        try:
            return path.stat().st_size if path.exists() else 0
        except OSError:
            return 0

    def audio_exists(self, path: Path, min_bytes: int = 1000) -> bool:
        """Checks whether audio file exists and has stable size."""
        if not path.exists():
            return False
        try:
            return path.stat().st_size > min_bytes
        except OSError:
            return False

    def save_state(self, path: Path, state_dict: dict[str, object] | SynthesisStats) -> None:
        """Saves processing state metadata in JSON format."""
        if isinstance(state_dict, SynthesisStats):
            payload: dict[str, object] = {
                "char_count": state_dict.char_count,
                "word_count": state_dict.word_count,
                "segment_count": state_dict.segment_count,
                "duration_sec": state_dict.duration_sec,
                "audio_duration_sec": state_dict.audio_duration_sec,
                "rtf": state_dict.rtf,
                "speed_factor": state_dict.speed_factor,
                "chars_per_sec": state_dict.chars_per_sec,
            }
        else:
            payload = state_dict

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
