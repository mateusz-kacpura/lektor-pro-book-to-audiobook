"""Repository managing Markdown TTS Studio snippets and history."""

import json
import logging
from pathlib import Path
from typing import Sequence, cast

from ...application.ports.storage_ports import StudioHistoryRepositoryProtocol
from ...domain.studio_models import StudioItem

logger = logging.getLogger(__name__)


class FileSystemStudioHistoryRepository(StudioHistoryRepositoryProtocol):
    """Repository implementing StudioRepositoryProtocol."""

    def __init__(
        self,
        history_file: Path,
        audio_dir: Path,
    ) -> None:
        self.history_file = history_file.resolve()
        self.audio_dir = audio_dir.resolve()
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def get_history(self) -> Sequence[StudioItem]:
        """Retrieves list of recording history items and verifies file existence."""
        if self.history_file.exists():
            try:
                data = json.loads(self.history_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    items: list[StudioItem] = []
                    for it in data:
                        if isinstance(it, dict):
                            typed_it = cast(dict[str, object], it)
                            safe_id = str(typed_it.get("id", ""))
                            wav_path = self.audio_dir / f"{safe_id}.wav"
                            audio_exists = wav_path.exists() and wav_path.stat().st_size > 1000
                            typed_it["audio_exists"] = audio_exists
                            if audio_exists:
                                typed_it["file_size_kb"] = round(wav_path.stat().st_size / 1024, 1)
                            items.append(StudioItem.from_dict(typed_it))
                    return items
            except Exception as e:
                logger.error(f"[Studio History Error] {e}")
                return []
        return []

    def save_history(self, items: Sequence[StudioItem | dict[str, object]]) -> None:
        """Persists recording history list to JSON file."""
        serialized = [
            it.to_dict() if isinstance(it, StudioItem) else it
            for it in items
        ]
        self.history_file.write_text(
            json.dumps(serialized, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_or_update_item(self, item: StudioItem | dict[str, object]) -> None:
        """Adds or updates recording history item at the beginning of the list."""
        typed_item = item if isinstance(item, StudioItem) else StudioItem.from_dict(item)
        safe_id = typed_item.id
        history = [it for it in self.get_history() if it.id != safe_id]
        history.insert(0, typed_item)
        self.save_history(history)

    def delete_item(self, item_id: str) -> bool:
        """Deletes recording item by ID and removes associated audio file."""
        import re
        safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "", item_id)
        wav_path = self.audio_dir / f"{safe_id}.wav"
        if wav_path.exists():
            try:
                wav_path.unlink()
            except Exception as e:
                logger.warning(f"Nie udało się usunąć pliku audio {wav_path}: {e}")

        history = [it for it in self.get_history() if it.id != safe_id]
        self.save_history(history)
        return True

