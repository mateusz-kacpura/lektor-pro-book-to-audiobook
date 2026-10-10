"""
Testy End-to-End (E2E) dla modułów Web GUI API (FastAPI).
"""

import unittest
from fastapi.testclient import TestClient
from lektor.infrastructure.gui_app import app


class TestGuiE2E(unittest.TestCase):
    client: TestClient

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_e2e_get_status_endpoint(self) -> None:
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_pages", data)
        self.assertIn("progress", data)
        self.assertIn("pages", data)
        self.assertIsInstance(data["pages"], list)

    def test_e2e_notes_crud_lifecycle(self) -> None:
        test_note_id = "e2e_test_note"
        test_content = "# Notatka E2E\nPrzykładowa treść do weryfikacji architektury."

        save_res = self.client.post("/api/notes", json={"note_id": test_note_id, "content": test_content})
        self.assertEqual(save_res.status_code, 200)
        self.assertEqual(save_res.json()["status"], "saved")

        get_res = self.client.get(f"/api/notes/{test_note_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["content"], test_content)

    def test_e2e_studio_history_endpoint(self) -> None:
        res = self.client.get("/api/studio/history")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("items", data)
        self.assertIn("count", data)

    def test_e2e_index_page_returns_html(self) -> None:
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers.get("content-type", ""))

    def test_e2e_audio_path_traversal_protection(self) -> None:
        traversal_res = self.client.get("/audio/..%2F..%2Frun_gui.py")
        self.assertEqual(traversal_res.status_code, 404)

        traversal_studio = self.client.get("/audio/studio/..%2F..%2Frun_gui.py")
        self.assertEqual(traversal_studio.status_code, 404)


if __name__ == "__main__":
    unittest.main()