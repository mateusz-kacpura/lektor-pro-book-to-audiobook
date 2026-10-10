"""
tests.unit.test_conversion_models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Testy jednostkowe encji, obiektów wartości i maszyn stanów nowej funkcjonalności (Reguły 1-15).
"""

import unittest
from pathlib import Path

from lektor.domain.conversion_models import (
    BookSlug,
    ConversionJob,
    ConversionTaskState,
    create_page_number,
    format_page_filename,
    validate_book_slug,
)
from lektor.domain.normalizers.glossary import TechnicalGlossaryService
from lektor.domain.validators.markdown_validator import MarkdownPageValidationService


class TestConversionModelsAndValidators(unittest.TestCase):
    """Testy modeli domenowych i walidatorów rurociągu konwersji."""

    def test_book_slug_validation_success(self) -> None:
        slug = validate_book_slug("kubernetes_patterns_2026")
        self.assertEqual(str(slug), "kubernetes_patterns_2026")
        self.assertIsInstance(slug, str)

    def test_book_slug_validation_failures(self) -> None:
        invalid_slugs = ["My Book!", "slug with spaces", "slug-with-hyphens", "slug@domain"]
        for inv in invalid_slugs:
            with self.assertRaises(ValueError):
                validate_book_slug(inv)

    def test_page_number_and_formatting(self) -> None:
        pn = create_page_number(42)
        self.assertEqual(int(pn), 42)
        fname = format_page_filename(pn, prefix="page_", ext=".jpg", digits=3)
        self.assertEqual(fname, "page_042.jpg")

        with self.assertRaises(ValueError):
            create_page_number(0)

    def test_conversion_job_state_machine(self) -> None:
        job = ConversionJob.create(BookSlug("cloud_go"), Path("test.pdf"))
        self.assertEqual(job.state, ConversionTaskState.IDLE)
        self.assertFalse(job.is_terminal())

        job.transition_to(ConversionTaskState.SPLITTING_PDF)
        self.assertEqual(job.state, ConversionTaskState.SPLITTING_PDF)

        job.transition_to(ConversionTaskState.TRANSLATING)
        self.assertEqual(job.state, ConversionTaskState.TRANSLATING)

        # Rejestracja stron
        p1 = create_page_number(1)
        p2 = create_page_number(2)
        job.mark_page_completed(p1)
        self.assertEqual(job.completed_pages, 1)

        job.mark_page_failed(p2, "Vision model timeout")
        self.assertEqual(len(job.failed_pages), 1)
        self.assertEqual(job.failed_pages[2], "Vision model timeout")

        # Anulowanie
        job.request_cancellation()
        self.assertTrue(job.cancellation_requested)

        job.transition_to(ConversionTaskState.COMPLETED)
        self.assertTrue(job.is_terminal())

    def test_markdown_page_validation_service(self) -> None:
        validator = MarkdownPageValidationService()

        # Poprawna strona
        valid_page = """# Rozdział 1: Cloud Native
Oto kod programu:
```go
package main
func main() {}
```
Oraz diagram:
```mermaid
flowchart TD
    A[Klient] --> B[Serwer]
```
"""
        self.assertTrue(validator.validate_page_integrity(valid_page))

        # Niezbalansowane znaczniki kodu
        broken_code = """# Rozdział
```go
func main() {}
Brak domknięcia bloku kodu
"""
        self.assertFalse(validator.validate_page_integrity(broken_code))

        # Nieprawidłowy diagram Mermaid (nieznany typ i niedomknięty nawias)
        broken_mermaid = """# Diagram
```mermaid
nieznanyTyp TD
    A[Brak nawiasu --> B
```
"""
        self.assertFalse(validator.validate_page_integrity(broken_mermaid))

    def test_technical_glossary_protection(self) -> None:
        glossary = TechnicalGlossaryService(terms=["Kubernetes", "gRPC", "Circuit Breaker"])
        raw = "Wdrożenie Kubernetes wspiera komunikację gRPC oraz wzorzec Circuit Breaker."

        protected, replacements = glossary.protect_technical_terms(raw)
        self.assertNotIn("Kubernetes", protected)
        self.assertNotIn("gRPC", protected)
        self.assertIn("__LEKTOR_TERM_", protected)

        restored = glossary.restore_technical_terms(protected, replacements)
        self.assertEqual(restored, raw)

    def test_translated_markdown_page_from_raw_markdown_factory(self) -> None:
        from lektor.domain.conversion_models import TranslatedMarkdownPage

        raw_input = """```markdown
# Rozdział 3: Architektura Mikroserwisów

Przykładowy listing w Go:
```go
package main

import "fmt"

func main() {
    // Komentarz po polsku
    fmt.Println("Witaj w chmurze!")
}
```

Poniższy diagram przedstawia architekturę:
```mermaid
sequenceDiagram
    Client->>Gateway: Request
    Gateway->>Service: Forward
```

Podsumowanie strony.
```"""
        p_num = create_page_number(7)
        page = TranslatedMarkdownPage.from_raw_markdown(
            page_number=p_num,
            raw_markdown=raw_input,
            tokens_per_sec=42.5,
        )

        self.assertEqual(int(page.page_number), 7)
        self.assertEqual(page.tokens_per_sec, 42.5)
        # Markdown wrapper powinien zostać usunięty
        self.assertFalse(page.markdown_content.startswith("```markdown"))
        self.assertTrue(page.markdown_content.startswith("# Rozdział 3"))
        # 1 diagram Mermaid typu sequenceDiagram
        self.assertEqual(len(page.diagrams), 1)
        self.assertEqual(page.diagrams[0].diagram_type, "sequencediagram")
        self.assertIn("Client->>Gateway: Request", page.diagrams[0].raw_code)
        # 1 blok kodu źródłowego (Go)
        self.assertEqual(page.code_blocks_count, 1)
