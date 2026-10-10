"""Repository managing user notes and highlights."""

import re
from pathlib import Path

from ...application.ports.storage_ports import NotesRepositoryProtocol


class FileSystemNotesRepository(NotesRepositoryProtocol):
    """Repository implementing NotesRepositoryProtocol."""

    def __init__(self, notes_dir: Path) -> None:
        self.notes_dir = notes_dir.resolve()
        self.notes_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_id(self, note_id: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_\-]", "", note_id)
        return safe if safe else "global"

    def get_note(self, note_id: str) -> str:
        """Retrieves note content from notes repository."""
        safe_id = self._sanitize_id(note_id)
        note_file = self.notes_dir / f"{safe_id}.md"
        if note_file.exists():
            return note_file.read_text(encoding="utf-8")
        return ""

    def save_note(self, note_id: str, content: str) -> Path:
        """Saves note content to notes repository."""
        safe_id = self._sanitize_id(note_id)
        note_file = self.notes_dir / f"{safe_id}.md"
        note_file.write_text(content, encoding="utf-8")
        return note_file
