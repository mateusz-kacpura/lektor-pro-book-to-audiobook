"""
tests.benchmark.test_benchmark_gui_throughput
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Testy benchmarkowe przepustowości i alokacji pamięci serwera Web GUI (FastAPI).
Weryfikacja braku wycieków pamięci przy obsłudze wielu żądań HTTP.
"""

import unittest

from fastapi.testclient import TestClient

from lektor.infrastructure.gui_app import app
from tests.benchmark.profiler import ResourceProfiler


class TestBenchmarkGuiThroughput(unittest.TestCase):
    """Testy obciążeniowe endpointów HTTP adaptera Web GUI."""

    client: TestClient

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_benchmark_gui_status_endpoint_memory_leak(self) -> None:
        """Weryfikuje brak wycieków pamięci przy 50 zapytaniach do endpointu /api/status."""
        profiler = ResourceProfiler(
            name="Web GUI: 50 żądań do /api/status",
            max_allowed_heap_bytes=25 * 1024 * 1024,
            max_allowed_leak_growth_bytes=1024 * 1024,  # Norma wycieku: poniżej 1 MB po 50 żądaniach
        )

        def make_request() -> None:
            resp = self.client.get("/api/status")
            self.assertEqual(resp.status_code, 200)

        res = profiler.run(make_request, iterations=50, warmup=5)

        self.assertFalse(res.memory_norm_exceeded, f"Przekroczono limit pamięci heap: {res.peak_heap_bytes} B")
        self.assertFalse(res.leak_detected, f"Wykryto wyciek pamięci w Web GUI! Delta: {res.heap_delta_bytes} B")
        # Średni czas na żądanie powinien być poniżej 300 ms przy aktywnym profilowaniu tracemalloc
        avg_request_ms = (res.duration_sec / res.iterations) * 1000.0
        self.assertLess(avg_request_ms, 300.0, f"Zbyt wolna obsługa żądań: {avg_request_ms:.2f} ms / req")
