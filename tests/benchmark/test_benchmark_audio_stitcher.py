"""
tests.benchmark.test_benchmark_audio_stitcher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Testy benchmarkowe łączenia i czyszczenia audio (NumPy & Audio Stitcher).
Pomiary alokacji tablic w pamięci RAM, profilowanie CPU, weryfikacja norm i brak wycieków.
"""

import unittest

import numpy as np

from lektor.adapters.audio.cleaner import SileroAudioCleaner
from lektor.adapters.audio.stitcher import NumpyAudioStitcher
from lektor.domain.audio_models import AudioBuffer, make_audio_buffer
from tests.benchmark.profiler import ResourceProfiler


class TestBenchmarkAudioStitcher(unittest.TestCase):
    """Testy wydajnościowe operacji wektorowych i alokacji buforów dźwiękowych."""

    stitcher: NumpyAudioStitcher
    cleaner: SileroAudioCleaner
    sample_segments: list[tuple[AudioBuffer, int]]

    @classmethod
    def setUpClass(cls) -> None:
        cls.stitcher = NumpyAudioStitcher(sample_rate=24000)
        cls.cleaner = SileroAudioCleaner(sample_rate=24000)

        # Tworzymy 20 syntetycznych segmentów audio z pauzą 250 ms (każdy po 2 sekundy @ 24kHz = 48 000 próbek)
        cls.sample_segments = []
        for i in range(20):
            t = np.linspace(0, 2.0, 48000, endpoint=False, dtype=np.float32)
            sine_wave = (0.5 * np.sin(2 * np.pi * 440 * (i + 1) * 0.1 * t)).astype(np.float32)
            cls.sample_segments.append((make_audio_buffer(sine_wave), 250))

    def test_benchmark_audio_stitch_allocation_and_norm(self) -> None:
        """Weryfikuje alokację pamięci i czas CPU podczas łączenia 20 segmentów audio."""
        profiler = ResourceProfiler(
            name="Łączenie 20 segmentów audio (40 sekund @ 24kHz)",
            max_allowed_heap_bytes=35 * 1024 * 1024,  # Norma: max 35 MB dla operacji na buforach
            max_allowed_leak_growth_bytes=1024 * 1024,
        )

        def run_stitch() -> None:
            result = self.stitcher.stitch_segments(self.sample_segments)
            self.assertGreater(len(result), 900000)

        res = profiler.run(run_stitch, iterations=1, warmup=1)

        self.assertFalse(res.memory_norm_exceeded, f"Przekroczono limit pamięci: {res.peak_heap_bytes} B")
        self.assertFalse(res.leak_detected, "Wykryto nieoczekiwany wyciek w NumpyAudioStitcher!")
        self.assertLess(res.duration_sec, 2.0, "Łączenie próbek NumPy trwało zbyt długo!")

    def test_benchmark_audio_cleaner_memory_leak(self) -> None:
        """Weryfikuje brak wycieków pamięci przy wielokrotnym czyszczeniu próbek."""
        profiler = ResourceProfiler(
            name="Wykrywanie wycieków pamięci: SileroAudioCleaner",
            max_allowed_heap_bytes=20 * 1024 * 1024,
            max_allowed_leak_growth_bytes=1024 * 1024,  # Norma wycieku: poniżej 1 MB po 25 cyklach
        )

        test_waveform = make_audio_buffer(np.asarray(self.sample_segments[0][0]).copy())

        def run_clean_cycle() -> None:
            cleaned = self.cleaner.clean_tail(test_waveform, sample_rate=24000)
            self.assertEqual(len(cleaned), len(test_waveform))

        res = profiler.run(run_clean_cycle, iterations=25, warmup=2)

        self.assertFalse(
            res.leak_detected,
            f"Wykryto wyciek pamięci w filtrach SileroAudioCleaner! Delta: {res.heap_delta_bytes} B. "
            f"Traces: {res.top_allocations}",
        )
