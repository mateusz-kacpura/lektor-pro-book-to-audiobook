"""
Testy jednostkowe encji i obiektów wartości (Domain Models).
"""

import unittest

from lektor.domain.audio_models import (
    AudioSpec,
    PageNumber,
    SpeechSegment,
    SynthesisStats,
)
from lektor.domain.book_models import BookPageMetadata


class TestDomainModels(unittest.TestCase):
    """Weryfikacja niezmienników i zachowania modeli domenowych."""

    def test_speech_segment_defaults_and_immutability(self) -> None:
        seg = SpeechSegment(text="Witaj świecie", lang="pl")
        self.assertEqual(seg.text, "Witaj świecie")
        self.assertEqual(seg.lang, "pl")
        self.assertEqual(seg.pause_after_ms, 350)
        self.assertFalse(seg.is_header)
        self.assertFalse(seg.is_code)

        # Frozen dataclass zapobiega mutacji
        with self.assertRaises(Exception):
            seg.text = "Nowy tekst"  # type: ignore

    def test_speech_segment_empty_lang_fallback(self) -> None:
        seg = SpeechSegment(text="Test", lang="")
        self.assertEqual(seg.lang, "pl")

    def test_speech_segment_negative_pause_sanitization(self) -> None:
        seg = SpeechSegment(text="Test", lang="pl", pause_after_ms=-50)
        self.assertEqual(seg.pause_after_ms, 0)

    def test_audio_spec_validations(self) -> None:
        spec = AudioSpec(sample_rate=24000, audio_format="wav", target_peak=0.95)
        self.assertEqual(spec.sample_rate, 24000)
        self.assertEqual(spec.audio_format, "wav")
        self.assertEqual(spec.target_peak, 0.95)

        with self.assertRaises(ValueError):
            AudioSpec(sample_rate=0)

        with self.assertRaises(ValueError):
            AudioSpec(target_peak=0.0)

        with self.assertRaises(ValueError):
            AudioSpec(target_peak=1.5)

    def test_synthesis_stats_metrics(self) -> None:
        stats = SynthesisStats(
            char_count=500,
            word_count=80,
            segment_count=5,
            duration_sec=10.0,
            audio_duration_sec=20.0,
        )
        self.assertEqual(stats.rtf, 0.5)
        self.assertEqual(stats.speed_factor, 2.0)
        self.assertEqual(stats.chars_per_sec, 50.0)

    def test_synthesis_stats_zero_duration_safe(self) -> None:
        stats = SynthesisStats(
            char_count=0,
            word_count=0,
            segment_count=0,
            duration_sec=0.0,
            audio_duration_sec=0.0,
        )
        self.assertEqual(stats.rtf, 0.0)
        self.assertEqual(stats.speed_factor, 0.0)
        self.assertEqual(stats.chars_per_sec, 0.0)

    def test_book_page_metadata(self) -> None:
        meta = BookPageMetadata(
            title="Wstęp do Cloud Native",
            page_number=PageNumber(1),
            original_file="book/page-001.jpg",
            scan_file="/book/page-001.jpg",
        )
        self.assertEqual(meta.page_number, 1)
        self.assertEqual(meta.title, "Wstęp do Cloud Native")


if __name__ == "__main__":
    unittest.main()
