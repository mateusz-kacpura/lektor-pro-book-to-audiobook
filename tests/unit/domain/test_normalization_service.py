"""
Testy jednostkowe usługi normalizacji tekstu (TextNormalizationService).
Weryfikacja reguł Markdown, kodu Go, liczb, słownika IT i detekcji języków.
"""

import unittest

from lektor.domain.normalization import TextNormalizationService


class TestNormalizationService(unittest.TestCase):
    """Weryfikacja zachowania reguł normalizacji bez żadnego I/O."""

    def setUp(self) -> None:
        self.service = TextNormalizationService(code_mode="spoken", language_mode="bilingual")

    def test_empty_or_whitespace_returns_empty_list(self) -> None:
        self.assertEqual(self.service.normalize(""), [])
        self.assertEqual(self.service.normalize("   \n\n\t  "), [])

    def test_markdown_cleaning_headers_and_formatting(self) -> None:
        md = "# Rozdział 1 — Wstęp\n\nTo jest **bardzo ważny** tekst z [linkiem](http://example.com)."
        segments = self.service.normalize(md)
        self.assertGreater(len(segments), 0)

        # Sprawdź, czy znaczniki Markdown zostały usunięte
        full_text = " ".join(s.text for s in segments)
        self.assertNotIn("**", full_text)
        self.assertNotIn("[linkiem]", full_text)
        self.assertNotIn("http://", full_text)

    def test_number_verbalization_in_polish(self) -> None:
        md = "Mamy 15 węzłów w klastrze oraz 200 podów."
        segments = self.service.normalize(md)
        full_text = " ".join(s.text for s in segments)
        self.assertIn("piętnaście", full_text)
        self.assertIn("dwieście", full_text)
        self.assertNotIn(" 15 ", full_text)
        self.assertNotIn(" 200 ", full_text)

    def test_go_code_block_verbalization(self) -> None:
        md = "Oto przykład w języku Go:\n\n```go\nfunc main() {\n    err := doSomething()\n}\n```"
        segments = self.service.normalize(md)
        code_segs = [s for s in segments if s.is_code]
        self.assertGreater(len(code_segs), 0)
        code_text = code_segs[0].text
        self.assertIn("funkcj", code_text)
        self.assertIn("deklaracja i przypisanie", code_text)

    def test_bilingual_bracket_clause_extraction(self) -> None:
        md = "Przetwarzanie natywne dla chmury *(cloud native computing)* jest nowoczesne."
        segments = self.service.normalize(md)
        self.assertGreater(len(segments), 1)
        # Przynajmniej jeden segment powinien zawierać angielski zwrot
        english_segments = [s for s in segments if "cloud native computing" in s.text.lower()]
        self.assertTrue(len(english_segments) >= 1)

    def test_footnotes_and_frontmatter_removed(self) -> None:
        md = """---
title: Test
---
Treść główna[^1].

[^1]: To jest przypis dolny.
"""
        segments = self.service.normalize(md)
        full_text = " ".join(s.text for s in segments)
        self.assertIn("Treść główna", full_text)
        self.assertNotIn("To jest przypis dolny", full_text)
        self.assertNotIn("[^1]", full_text)

    def test_custom_code_explainer_injection(self) -> None:
        class DummyExplainer:
            def explain_inline(self, code: str) -> str:
                return f"ZASTAPIONY INLINE {code}"

            def explain_block(self, code: str, lang: str = "", mode: str = "spoken") -> str:
                return f"ZASTAPIONY BLOK {lang}"

        custom_service = TextNormalizationService(
            code_mode="spoken",
            language_mode="bilingual",
            code_explainer=DummyExplainer(),
        )

        md = "Kod w tekście\n\n```python\nprint('hello')\n```"
        segments = custom_service.normalize(md)
        texts = [s.text for s in segments]
        self.assertTrue(any("ZASTAPIONY BLOK python" in t for t in texts))


if __name__ == "__main__":
    unittest.main()
