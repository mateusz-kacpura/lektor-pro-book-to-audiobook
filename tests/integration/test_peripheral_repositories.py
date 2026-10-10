"""
Testy jednostkowe adapterów repozytoriów peryferyjnych (Notes, Studio).
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from lektor.adapters.storage.notes_repository import FileSystemNotesRepository
from lektor.adapters.storage.studio_repository import FileSystemStudioHistoryRepository


class TestPeripheralRepositories(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_notes_repository_crud(self) -> None:
        notes_dir = self.temp_dir / "notes"
        repo = FileSystemNotesRepository(notes_dir=notes_dir)

        self.assertEqual(repo.get_note("test_note"), "")
        saved_file = repo.save_note("test_note", "# Treść notatki testowej")
        self.assertTrue(saved_file.exists())
        self.assertEqual(repo.get_note("test_note"), "# Treść notatki testowej")

    def test_studio_history_repository_crud(self) -> None:
        history_file = self.temp_dir / "studio" / "history.json"
        audio_dir = self.temp_dir / "studio" / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        repo = FileSystemStudioHistoryRepository(history_file=history_file, audio_dir=audio_dir)
        self.assertEqual(len(repo.get_history()), 0)

        dummy_wav = audio_dir / "tts_test.wav"
        dummy_wav.write_bytes(b"\x00" * 2000)

        item: dict[str, object] = {
            "id": "tts_test",
            "title": "Nagranie testowe",
            "markdown": "# Test",
        }
        repo.save_history([item])

        history = repo.get_history()
        self.assertEqual(len(history), 1)
        self.assertTrue(history[0].get("audio_exists"))

        item2: dict[str, object] = {"id": "tts_test_2", "title": "Drugi test", "markdown": "Treść 2"}
        repo.add_or_update_item(item2)
        self.assertEqual(len(repo.get_history()), 2)

        repo.delete_item("tts_test")
        self.assertEqual(len(repo.get_history()), 1)
        self.assertFalse(dummy_wav.exists())


if __name__ == "__main__":
    unittest.main()