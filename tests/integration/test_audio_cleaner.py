"""
Testy jednostkowe adaptera SileroAudioCleaner i odwrócenia zależności w ChatterboxSynthesizer.
Weryfikacja zgodności z AudioCleanerProtocol, izolacji I/O i poprawnej filtracji.
"""

import unittest

import numpy as np

from lektor.adapters.audio.cleaner import SileroAudioCleaner
from lektor.adapters.tts.mock_engine import MockTTSEngine
from lektor.adapters.tts.universal_engine import UniversalTTSEngine, UniversalTTSEngineOptions
from lektor.application.ports.audio_ports import AudioCleanerProtocol
from lektor.domain.audio_models import AudioBuffer, make_audio_buffer


class MockAudioCleaner(AudioCleanerProtocol):
    """Atrapa oczyszczacza audio do weryfikacji DIP."""

    def __init__(self) -> None:
        self.clean_calls: list[int] = []

    def clean_tail(self, audio: AudioBuffer, sample_rate: int = 24000) -> AudioBuffer:
        self.clean_calls.append(len(audio))
        # Zwraca połowę próbek jako symulację przycięcia
        return make_audio_buffer(audio[: len(audio) // 2])


class TestAudioCleanerAndDIP(unittest.TestCase):
    def setUp(self) -> None:
        self.cleaner = SileroAudioCleaner(sample_rate=24000)

    def test_short_audio_returns_unchanged(self) -> None:
        # Poniżej 0.2s (4800 próbek przy 24kHz) cleaner powinien zwrócić audio bez zmian
        short_buf = make_audio_buffer(np.ones(1000, dtype=np.float32))
        cleaned = self.cleaner.clean_tail(short_buf, sample_rate=24000)
        np.testing.assert_array_equal(short_buf, cleaned)

    def test_fade_in_and_fade_out_applied(self) -> None:
        # Bufor 1 sekunda (24000 próbek)
        ones_buf = make_audio_buffer(np.ones(24000, dtype=np.float32))
        cleaned = self.cleaner.clean_tail(ones_buf, sample_rate=24000)

        self.assertIsInstance(np.asarray(cleaned), np.ndarray)
        self.assertEqual(np.asarray(cleaned).dtype, np.float32)
        # Początek powinien zaczynać się w okolicach 0 (fade-in)
        self.assertLess(float(cleaned[0]), 0.1)
        # Koniec powinien kończyć się w okolicach 0 (fade-out)
        self.assertLess(float(cleaned[-1]), 0.1)

    def test_silero_cleaner_handles_tail_cleaning(self) -> None:
        buf = make_audio_buffer(np.ones(1000, dtype=np.float32))
        res = self.cleaner.clean_tail(buf, sample_rate=24000)
        self.assertEqual(len(res), len(buf))

    def test_universal_engine_accepts_injected_cleaner_and_fallback(self) -> None:
        mock_cleaner = MockAudioCleaner()
        mock_fallback = MockTTSEngine(sample_rate=24000)

        synth = UniversalTTSEngine(
            UniversalTTSEngineOptions(
                cleaner=mock_cleaner,
                fallback_synth=mock_fallback,
                trim_trailing_silence=True,
            )
        )

        self.assertIs(synth.cleaner, mock_cleaner)
        self.assertIs(synth.fallback_synth, mock_fallback)

        audio_out = synth.synthesize_segment("Test mowy")
        self.assertEqual(len(mock_fallback.synthesized_calls), 1)
        self.assertEqual(mock_fallback.synthesized_calls[0][0], "Test mowy")
        self.assertIsInstance(audio_out, np.ndarray)


if __name__ == "__main__":
    unittest.main()
