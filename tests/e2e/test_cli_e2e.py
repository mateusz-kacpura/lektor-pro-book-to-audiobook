"""
Testy End-to-End (E2E) dla interfejsu wiersza poleceń CLI (main.py).
Weryfikacja pełnych ścieżek użytkownika z wstrzykiwaniem kontenera IoC (DIP)
oraz użyciem silnika Mock TTS do natychmiastowej weryfikacji.
"""

import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path

from lektor.adapters.cli.main import main
from lektor.infrastructure.container import default_container


class TestCliE2E(unittest.TestCase):
    """Testy End-to-End ścieżek CLI."""

    def test_e2e_cli_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            md_path = Path(tmp_dir) / "page_001.md"
            md_path.write_text(
                "# Rozdział 1: Wprowadzenie do Cloud Native\n\n"
                "Systemy rozproszone wymagają architektury `stateless`.\n"
                "Poniższy kod przedstawia serwer w języku Go:\n\n"
                "```go\n"
                "func main() {\n"
                "    println(\"Witaj świecie\")\n"
                "}\n"
                "```\n",
                encoding="utf-8",
            )

            stdout_buf = StringIO()
            old_stdout = sys.stdout
            try:
                sys.stdout = stdout_buf
                exit_code = main(["preview", str(md_path)], container=default_container)
            finally:
                sys.stdout = old_stdout

            output = stdout_buf.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("PODGLĄD NORMALIZACJI", output)
            self.assertIn("Segmenty:", output)
            self.assertIn("Rozdział", output)

    def test_e2e_cli_single_mock_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            md_path = tmp_path / "page_042.md"
            md_path.write_text(
                "# Strona 42\n\nArchitektura mikroserwisów w chmurze.\n",
                encoding="utf-8",
            )
            out_dir = tmp_path / "audio_out"

            stdout_buf = StringIO()
            old_stdout = sys.stdout
            try:
                sys.stdout = stdout_buf
                exit_code = main(
                    [
                        "single",
                        str(md_path),
                        "-o",
                        str(out_dir),
                        "--mock",
                    ],
                    container=default_container,
                )
            finally:
                sys.stdout = old_stdout

            output = stdout_buf.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Wygenerowano audio", output)

            expected_wav = out_dir / "page_042.wav"
            expected_txt = out_dir / "page_042_normalized.txt"
            self.assertTrue(expected_wav.exists())
            self.assertTrue(expected_txt.exists())
            self.assertGreater(expected_wav.stat().st_size, 1000)

    def test_e2e_cli_batch_mock_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            pages_dir = tmp_path / "pages"
            pages_dir.mkdir()
            (pages_dir / "page_001.md").write_text("# Strona 1\nPierwsza strona.", encoding="utf-8")
            (pages_dir / "page_002.md").write_text("# Strona 2\nDruga strona.", encoding="utf-8")
            out_dir = tmp_path / "audio_out"

            stdout_buf = StringIO()
            old_stdout = sys.stdout
            try:
                sys.stdout = stdout_buf
                exit_code = main(
                    [
                        "batch",
                        str(pages_dir),
                        "-o",
                        str(out_dir),
                        "--mock",
                    ],
                    container=default_container,
                )
            finally:
                sys.stdout = old_stdout

            output = stdout_buf.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Zakończono syntezę wsadową: przetworzono 2 stron", output)

            self.assertTrue((out_dir / "page_001.wav").exists())
            self.assertTrue((out_dir / "page_002.wav").exists())

    def test_e2e_cli_books_list(self) -> None:
        stdout_buf = StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = stdout_buf
            exit_code = main(["books", "list"], container=default_container)
        finally:
            sys.stdout = old_stdout

        output = stdout_buf.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("UNIWERSALNY MAGAZYN KSIĄŻEK", output)


if __name__ == "__main__":
    unittest.main()