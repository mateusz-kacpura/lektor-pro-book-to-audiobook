"""
tests.integration.test_conversion_integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Testy integracyjne adapterów podziału PDF (PyMuPDF) oraz punktów końcowych Web GUI API (FastAPI).
"""

import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz
from fastapi.testclient import TestClient

from lektor.infrastructure.gui_app import app
from lektor.adapters.ocr.pdf_splitter import PyMuPdfSplitterAdapter


class TestConversionIntegration(unittest.TestCase):
    """Testy integracyjne komponentów I/O rurociągu konwersji i API."""

    client: TestClient
    temp_dir: Path
    sample_pdf_path: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.td.name)

        # Generowanie rzeczywistego, poprawnego pliku PDF z 2 stronami za pomocą PyMuPDF
        self.sample_pdf_path = self.temp_dir / "sample_tech_book.pdf"
        doc = fitz.open()
        p1 = doc.new_page()
        p1.insert_text((50, 50), "Strona 1: Architektura Cloud Native w Go")
        p2 = doc.new_page()
        p2.insert_text((50, 50), "Strona 2: Listing kodu func main()")
        doc.save(str(self.sample_pdf_path))
        doc.close()

    def tearDown(self) -> None:
        self.td.cleanup()

    def test_pymupdf_splitter_renders_real_scans(self) -> None:
        splitter = PyMuPdfSplitterAdapter()
        page_count = splitter.get_page_count(self.sample_pdf_path)
        self.assertEqual(page_count, 2)

        out_scans_dir = self.temp_dir / "scans"
        scans = splitter.split_pdf(self.sample_pdf_path, out_scans_dir, dpi=150)

        self.assertEqual(len(scans), 2)
        self.assertEqual(int(scans[0].page_number), 1)
        self.assertEqual(int(scans[1].page_number), 2)
        self.assertTrue(scans[0].scan_path.exists())
        self.assertTrue(scans[1].scan_path.exists())
        self.assertGreater(scans[0].scan_path.stat().st_size, 500)

    def test_api_books_and_active_book_endpoints(self) -> None:
        # 1. Pobranie listy książek
        resp = self.client.get("/api/books")
        self.assertEqual(resp.status_code, 200)
        books_data = resp.json()
        self.assertIsInstance(books_data, list)

        # 2. Przełączenie aktywnej książki
        switch_resp = self.client.post("/api/active-book", json={"slug": "cloud_native_go"})
        self.assertEqual(switch_resp.status_code, 200)
        active_data = switch_resp.json()
        self.assertEqual(active_data["slug"], "cloud_native_go")
        self.assertTrue(active_data["is_active"])

    def test_api_converter_start_and_cancel_endpoints(self) -> None:
        payload = {
            "pdf_path": str(self.sample_pdf_path),
            "book_slug": "integration_test_book",
            "dpi": 150,
        }
        start_res = self.client.post("/api/converter/start", json=payload)
        self.assertEqual(start_res.status_code, 200)
        data = start_res.json()
        self.assertIn("task_id", data)
        self.assertEqual(data["status"], "started")

        task_id = data["task_id"]

        # Anulowanie zadania
        cancel_res = self.client.post(f"/api/converter/cancel/{task_id}")
        self.assertEqual(cancel_res.status_code, 200)
        self.assertEqual(cancel_res.json()["status"], "cancellation_requested")

