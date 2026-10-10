"""
Testy integracyjne odwrócenia zależności (Dependency Injection) w warstwie FastAPI Web GUI.
"""

import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from lektor.adapters.gui.dependencies import get_gpu_telemetry, get_notes_repository, get_studio_history_repository
from lektor.application.dtos import BookMetadataDTO
from lektor.application.ports.storage_ports import NotesRepositoryProtocol
from lektor.domain.studio_models import StudioItem
from lektor.infrastructure.gui_app import app


class MockNotesRepository(NotesRepositoryProtocol):
    def __init__(self) -> None:
        self.notes: dict[str, str] = {}

    def get_note(self, note_id: str) -> str:
        return self.notes.get(note_id, "")

    def save_note(self, note_id: str, content: str) -> Path:
        self.notes[note_id] = content
        return Path(f"/virtual/notes/{note_id}.md")


class TestGuiDependencyInjection(unittest.TestCase):
    client: TestClient

    def setUp(self) -> None:
        self.mock_notes = MockNotesRepository()
        app.dependency_overrides[get_notes_repository] = lambda: self.mock_notes
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_notes_endpoint_uses_injected_dependency(self) -> None:
        save_res = self.client.post("/api/notes", json={"note_id": "di_note", "content": "Wstrzyknięta treść"})
        self.assertEqual(save_res.status_code, 200)
        self.assertIn("di_note", self.mock_notes.notes)
        self.assertEqual(self.mock_notes.notes["di_note"], "Wstrzyknięta treść")

        get_res = self.client.get("/api/notes/di_note")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["content"], "Wstrzyknięta treść")

    def test_switch_active_book_calls_injected_container_reset(self) -> None:
        class DummyContainer:
            def __init__(self) -> None:
                self.reset_called = False

            def reset_book_context(self, new_paths: object = None) -> None:
                self.reset_called = True

        class DummySwitchUseCase:
            def execute(self, cmd: object) -> BookMetadataDTO:
                return BookMetadataDTO(
                    slug="mock_book",
                    title="Mock Book",
                    total_pages=10,
                    audio_pages=0,
                    scan_pages=10,
                    is_active=True,
                )

        dummy_container = DummyContainer()
        from lektor.adapters.gui.dependencies import get_container, get_switch_active_book_use_case
        app.dependency_overrides[get_container] = lambda: dummy_container
        app.dependency_overrides[get_switch_active_book_use_case] = lambda: DummySwitchUseCase()

        resp = self.client.post("/api/active-book", json={"slug": "cloud_native_go"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(dummy_container.reset_called)

    def test_studio_stats_endpoint_uses_injected_telemetry_and_history(self) -> None:
        class DummyGpuTelemetry:
            def get_gpu_stats(self) -> tuple[float, float, float]:
                return 4096.0, 12288.0, 87.5

        class DummyStudioHistoryRepository:
            def get_history(self) -> list[StudioItem]:
                return [
                    StudioItem(id="new", title="Nowe", markdown="tekst", synth_time_sec=3.5),
                    StudioItem(id="old", title="Stare", markdown="tekst", synth_time_sec=5.5),
                ]

        app.dependency_overrides[get_gpu_telemetry] = lambda: DummyGpuTelemetry()
        app.dependency_overrides[get_studio_history_repository] = lambda: DummyStudioHistoryRepository()

        response = self.client.get("/api/studio/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["gpu"]["used_vram_mb"], 4096.0)
        self.assertEqual(data["gpu"]["total_vram_mb"], 12288.0)
        self.assertEqual(data["gpu"]["utilization_pct"], 87.5)
        self.assertEqual(data["stats"]["last_synthesis_sec"], 3.5)
        self.assertEqual(data["stats"]["average_synthesis_sec"], 4.5)
        self.assertEqual(data["stats"]["completed_syntheses"], 2)
    def test_get_status_uses_injected_use_case(self) -> None:
        from lektor.adapters.gui.dependencies import get_book_status_use_case
        from lektor.application.dtos import BookStatusDTO

        class DummyStatusUseCase:
            def execute(self, query: object = None) -> BookStatusDTO:
                return BookStatusDTO(
                    book_title="Injected Architecture Book",
                    total_pdf_pages=50,
                    markdown_pages_count=20,
                    is_batch_running=False,
                    is_stopping=False,
                    total_pages=20,
                    ready_count=15,
                    latest_ready_page="page_0015",
                    active_generation=None,
                    progress={"percent": 75.0},
                    current_params={"temperature": 0.33},
                    available_voices=[],
                    pages=[],
                )

        app.dependency_overrides[get_book_status_use_case] = lambda: DummyStatusUseCase()
        resp = self.client.get("/api/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["book_title"], "Injected Architecture Book")
        self.assertEqual(data["ready_count"], 15)


if __name__ == "__main__":
    unittest.main()