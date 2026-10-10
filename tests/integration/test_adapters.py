"""
Testy integracyjne adapterów (AudioStitcher, FileRepository, TTSEngineFactory).
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from lektor.adapters.audio.stitcher import NumpyAudioStitcher
from lektor.adapters.ocr.formatter import DefaultBookMarkdownFormatter
from lektor.adapters.storage.file_repository import FileSystemPageRepository
from lektor.adapters.tts.factory import TTSEngineFactory
from lektor.adapters.tts.mock_engine import MockTTSEngine
from lektor.domain.audio_models import make_audio_buffer, PageNumber


class TestAdapters(unittest.TestCase):
    def test_audio_stitcher_integration(self) -> None:
        stitcher = NumpyAudioStitcher(sample_rate=24000)

        chunk1 = make_audio_buffer(np.ones(2400, dtype=np.float32) * 0.5)
        chunk2 = make_audio_buffer(np.ones(2400, dtype=np.float32) * 0.3)
        segments = [(chunk1, 100), (chunk2, 0)]

        stitched = stitcher.stitch_segments(segments)
        self.assertGreater(len(stitched), 4800)

        duration = stitcher.get_duration_sec(stitched)
        self.assertGreater(duration, 0.2)

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "test_output.wav"
            saved = stitcher.save_audio(stitched, out_file)
            self.assertTrue(saved.exists())
            self.assertGreater(saved.stat().st_size, 1000)

    def test_file_repository_integration(self) -> None:
        repo = FileSystemPageRepository()

        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            p1 = base / "page_001.md"
            p2 = base / "page_002.md"
            p10 = base / "page_010.md"

            repo.write_markdown(p2, "# Strona 2")
            repo.write_markdown(p1, "# Strona 1")
            repo.write_markdown(p10, "# Strona 10")

            read_content = repo.read_markdown(p1)
            self.assertEqual(read_content, "# Strona 1")

            # Numeryczne sortowanie
            pages = repo.list_pages(base, pattern="page_*.md")
            self.assertEqual([p.name for p in pages], ["page_001.md", "page_002.md", "page_010.md"])

            # Zapis stanu
            state_file = base / "state.json"
            repo.save_state(state_file, {"status": "ok", "progress": 100})
            self.assertTrue(state_file.exists())

    def test_tts_factory_integration(self) -> None:
        engine = TTSEngineFactory.create(engine_type="mock")
        self.assertIsInstance(engine, MockTTSEngine)
        self.assertFalse(engine.is_loaded())
        engine.load_model()
        self.assertTrue(engine.is_loaded())
        samples = engine.synthesize_segment("Witaj świecie", lang="pl")
        self.assertGreater(len(samples), 0)

    def test_book_markdown_formatter_integration(self) -> None:
        formatter = DefaultBookMarkdownFormatter()
        result = formatter.format_markdown(
            raw_md="To jest treść rozdziału.",
            page_num=PageNumber(5),
            img_name="page-0005.jpg",
            book_dir_name="images_dir",
        )
        self.assertIn("# Strona 005", result)
        self.assertIn('"page_number": 5', result)
        self.assertIn("images_dir/page-0005.jpg", result)
        self.assertIn("To jest treść rozdziału.", result)

        # Test z parametryzowanym tytułem książki
        custom_formatter = DefaultBookMarkdownFormatter(default_book_title="Cloud Native in Go")
        custom_res = custom_formatter.format_markdown(
            raw_md="# Wprowadzenie\n\nTreść strony...",
            page_num=PageNumber(1),
            img_name="page-0001.jpg",
            book_dir_name="scans",
        )
        self.assertIn("Cloud Native in Go - Strona 1", custom_res)
        self.assertIn("# Strona 001 — Wprowadzenie", custom_res)


    def test_qwen_vision_adapter_lifecycle(self) -> None:
        from lektor.adapters.ocr.vision_adapter import QwenVisionTranslatorAdapter
        from lektor.domain.conversion_models import DocumentScan, create_page_number

        adapter = QwenVisionTranslatorAdapter(
            api_base_url="http://127.0.0.1:9999/v1",
            model_name="qwen2.5-vl:7b",
            timeout_sec=1.0,
        )
        self.assertEqual(adapter.model_name, "qwen2.5-vl:7b")

        dummy_scan = DocumentScan(
            page_number=create_page_number(1),
            scan_path=Path("non_existent_scan.jpg"),
        )
        with self.assertRaises(FileNotFoundError):
            adapter.translate_scan(dummy_scan)


if __name__ == "__main__":
    unittest.main()

