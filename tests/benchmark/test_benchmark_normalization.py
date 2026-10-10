"""
tests.benchmark.test_benchmark_normalization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Testy benchmarkowe usługi normalizacji tekstu (Domain Layer).
Badanie alokacji pamięci, profilowanie CPU, weryfikacja norm i wykrywanie wycieków pamięci.
"""

import unittest

from lektor.domain.normalization import TextNormalizationService
from tests.benchmark.profiler import ResourceProfiler


class TestBenchmarkNormalization(unittest.TestCase):
    """Testy wydajnościowe i pamięciowe TextNormalizationService."""

    service: TextNormalizationService
    large_technical_markdown: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.service = TextNormalizationService()
        # Generujemy reprezentatywny tekst techniczny o dużej objętości (~100 stron)
        snippet = """
# Rozdział 12: Architektura Cloud Native w języku Go

W architekturze microservices kluczowa jest zasada stateless.
Gdy system wdraża Kubernetes (k8s) oraz etcd, funkcja `func processRequest(ctx context.Context, id int) (Result, error)`
musi prawidłowo obsługiwać błędy:
```go
package main

import (
    "context"
    "fmt"
)

func main() {
    val := 42
    if err != nil {
        log.Fatalf("Critical error: %v", err)
    }
    defer cancel()
}
```
Złożoność obliczeniowa wynosi O(n log n). Zbadano 250 węzłów, z czego 99.9% odpowiedziało w czasie < 15ms.
Wersja protokołu v2.4.1 wspiera gRPC oraz load balancer z algorytmem round-robin.
"""
        cls.large_technical_markdown = snippet * 50  # ~50 powtórzeń dużego rozdziału

    def test_benchmark_normalization_allocation_and_cpu(self) -> None:
        """Weryfikuje alokację pamięci i czas CPU przy przetwarzaniu dużego tekstu."""
        profiler = ResourceProfiler(
            name="Normalizacja dużego tekstu Markdown",
            max_allowed_heap_bytes=25 * 1024 * 1024,  # Norma: max 25 MB heap dla 50 stron
            max_allowed_leak_growth_bytes=1024 * 1024,
        )

        def run_normalization() -> None:
            segments = self.service.normalize(self.large_technical_markdown)
            self.assertGreater(len(segments), 100)

        result = profiler.run(run_normalization, iterations=1, warmup=1)

        # Asercje norm pamięciowych i wycieków
        self.assertFalse(result.memory_norm_exceeded, f"Przekroczono normę pamięci heap: {result.peak_heap_bytes} B")
        self.assertFalse(result.leak_detected, "Wykryto wyciek pamięci podczas pojedynczej normalizacji!")
        self.assertLess(result.duration_sec, 5.0, "Normalizacja 50 stron trwała zbyt długo!")

    def test_benchmark_normalization_memory_leak(self) -> None:
        """Weryfikuje brak wycieków pamięci (memory leak) przy wielokrotnej normalizacji."""
        profiler = ResourceProfiler(
            name="Wykrywanie wycieków pamięci: Normalizacja tekstu",
            max_allowed_heap_bytes=30 * 1024 * 1024,
            max_allowed_leak_growth_bytes=2 * 1024 * 1024,  # Norma wycieku: poniżej 2 MB po 30 cyklach
        )

        # Pojedynczy krótszy tekst uruchamiany 30 razy w pętli
        small_text = """
Rozdział 5: Goroutines i kanały w Go.
Uruchomienie `go worker(ch)` alokuje stos o rozmiarze 2 KB.
Wskaźnik `*sync.WaitGroup` synchronizuje operacje wejścia/wyjścia.
Błąd: `if err != nil` zwraca kod błędu HTTP 500.
"""

        def run_cycle() -> None:
            self.service.normalize(small_text)

        result = profiler.run(run_cycle, iterations=30, warmup=3)

        self.assertFalse(
            result.leak_detected,
            f"Wykryto wyciek pamięci w normalizatorze tekstu! Alokacja wzrosła o {result.heap_delta_bytes} B. "
            f"Traces: {result.top_allocations}",
        )
        self.assertFalse(result.memory_norm_exceeded, "Przekroczono dozwolony szczyt alokacji pamięci.")
