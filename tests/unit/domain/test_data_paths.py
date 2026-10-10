"""
Testy jednostkowe centralnego magazynu ścieżek DataPaths (SSOT).
Weryfikacja reguł DIP, OCP, niewrażliwości na zmiany katalogów i obsługi LEKTOR_DATA_DIR.
"""

import os
import tempfile
import unittest
from pathlib import Path

from lektor.adapters.storage.book_repository import FileSystemBookRepository
from lektor.adapters.tts.cache import AudioSegmentCache
from lektor.infrastructure.config import (
    DataPaths,
    InfrastructureSettings,
    load_env_file,
)


class TestDataPaths(unittest.TestCase):
    """Testy jednostkowe DataPaths i architektury SSOT dla ścieżek."""

    def test_custom_data_dir_resolution(self) -> None:
        custom_base = Path("/custom/storage/path").resolve()
        paths = DataPaths.from_data_dir(custom_base)

        self.assertEqual(paths.data_dir, custom_base)
        self.assertEqual(paths.books_dir, custom_base / "books")
        self.assertEqual(paths.audio_dir, custom_base / "books" / paths.active_book_slug / "audio")
        self.assertEqual(paths.notes_dir, custom_base / "notes")
        self.assertEqual(paths.default_voice_path, custom_base / "audio.wav")
        self.assertEqual(paths.cache_dir, custom_base / "audio_book" / ".cache" / "segments")
        self.assertEqual(paths.studio_audio_dir, custom_base / "audio_book" / "studio")

    def test_env_var_override(self) -> None:
        original_env = os.environ.get("LEKTOR_DATA_DIR")
        test_env_path = str(Path(tempfile.gettempdir()) / "lektor_test_data")
        try:
            os.environ["LEKTOR_DATA_DIR"] = test_env_path
            paths = DataPaths.from_data_dir()
            self.assertEqual(paths.data_dir, Path(test_env_path).resolve())
            self.assertEqual(paths.books_dir, Path(test_env_path).resolve() / "books")
        finally:
            if original_env is not None:
                os.environ["LEKTOR_DATA_DIR"] = original_env
            else:
                os.environ.pop("LEKTOR_DATA_DIR", None)

    def test_infrastructure_settings_properties(self) -> None:
        infra = InfrastructureSettings()
        self.assertEqual(infra.data_dir, infra.data_paths.data_dir)
        self.assertEqual(infra.books_dir, infra.data_paths.books_dir)
        self.assertEqual(infra.audio_dir, infra.data_paths.audio_dir)
        self.assertEqual(infra.notes_dir, infra.data_paths.notes_dir)
        self.assertEqual(infra.default_voice_path, infra.data_paths.default_voice_path)

    def test_book_repository_uses_injected_path(self) -> None:
        custom_target = Path(tempfile.gettempdir()) / "custom_books"
        custom_repo = FileSystemBookRepository(books_dir=custom_target)
        self.assertEqual(custom_repo.books_dir, custom_target.resolve())

    def test_audio_cache_uses_injected_path(self) -> None:
        custom_cache_target = Path(tempfile.gettempdir()) / "custom_cache"
        custom_cache = AudioSegmentCache(cache_dir=custom_cache_target)
        self.assertEqual(custom_cache.cache_dir, custom_cache_target.resolve())

    def test_load_env_file(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".env", encoding="utf-8") as f:
            f.write("# Komentarz testowy\n")
            f.write("TEST_ENV_KEY_FOO=bar_value\n")
            f.write("TEST_ENV_KEY_QUOTED=\"quoted_val\"\n")
            temp_path = Path(f.name)

        try:
            load_env_file(temp_path)
            self.assertEqual(os.environ.get("TEST_ENV_KEY_FOO"), "bar_value")
            self.assertEqual(os.environ.get("TEST_ENV_KEY_QUOTED"), "quoted_val")
        finally:
            os.environ.pop("TEST_ENV_KEY_FOO", None)
            os.environ.pop("TEST_ENV_KEY_QUOTED", None)
            if temp_path.exists():
                temp_path.unlink()

    def test_infrastructure_settings_env_overrides(self) -> None:
        original_host = os.environ.get("LEKTOR_GUI_HOST")
        original_port = os.environ.get("LEKTOR_GUI_PORT")
        original_browser = os.environ.get("LEKTOR_AUTO_OPEN_BROWSER")
        try:
            os.environ["LEKTOR_GUI_HOST"] = "0.0.0.0"
            os.environ["LEKTOR_GUI_PORT"] = "9090"
            os.environ["LEKTOR_AUTO_OPEN_BROWSER"] = "false"

            infra = InfrastructureSettings()
            self.assertEqual(infra.gui_host, "0.0.0.0")
            self.assertEqual(infra.gui_port, 9090)
            self.assertFalse(infra.auto_open_browser)
        finally:
            if original_host is not None:
                os.environ["LEKTOR_GUI_HOST"] = original_host
            else:
                os.environ.pop("LEKTOR_GUI_HOST", None)
            if original_port is not None:
                os.environ["LEKTOR_GUI_PORT"] = original_port
            else:
                os.environ.pop("LEKTOR_GUI_PORT", None)
            if original_browser is not None:
                os.environ["LEKTOR_AUTO_OPEN_BROWSER"] = original_browser
            else:
                os.environ.pop("LEKTOR_AUTO_OPEN_BROWSER", None)
