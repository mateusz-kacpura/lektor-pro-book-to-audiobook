"""
Automated PDF conversion pipeline.
Extracts scans, performs OCR/vision translation, and prepares normalized markdown.
"""

import argparse
import sys
import time
from pathlib import Path

# Implementation note: see the surrounding code for the behavior described here.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from lektor.infrastructure.container import default_container
from lektor.application.dtos import StartConversionCommand
from lektor.domain.conversion_models import (
    ConversionJob,
    validate_book_slug,
)


def run_pipeline(
    pdf_path: Path,
    book_slug_raw: str,
    title: str,
    author: str,
    start_page: int | None = None,
    end_page: int | None = None,
    dpi: int = 300,
) -> None:
    slug = validate_book_slug(book_slug_raw)
    resolved_pdf = pdf_path.resolve()

    if not resolved_pdf.exists():
        print(f"[BĹÄ„D] Plik PDF nie istnieje: {resolved_pdf}", file=sys.stderr)
        sys.exit(1)

    print("=" * 70)
    print(" RUROCIÄ„G KONWERSJI PDF -> JPG (300 DPI) -> MARKDOWN (AI VISION)")
    print("=" * 70)
    print(f"Plik ĹşrĂłdĹ‚owy:  {resolved_pdf.name}")
    print(f"Rozmiar:        {resolved_pdf.stat().st_size / (1024 * 1024):.2f} MB")
    print(f"Docelowy slug:  {slug}")
    print(f"TytuĹ‚ ksiÄ…ĹĽki:  {title}")
    print(f"Autor:          {author}")
    print(f"Zakres stron:   od {start_page or 1} do {end_page or 'koĹ„ca dokumentu'}")
    print(f"RozdzielczoĹ›Ä‡:  {dpi} DPI")
    print("-" * 70)

    # Implementation note: see the surrounding code for the behavior described here.
    repo = default_container.get_book_repository()
    book = repo.get_book(str(slug))
    if book is None:
        print(f"[*] Inicjalizacja nowej ksiÄ…ĹĽki w repozytorium: '{slug}'...")
        book = repo.create_book(
            title=title,
            slug=str(slug),
            author=author,
            language="pl",
            description=f"Konwersja PDF ksiÄ…ĹĽki: {title} ({author})",
        )
    else:
        print(f"[*] Korzystanie z istniejÄ…cej ksiÄ…ĹĽki: {book.title}")

    # Implementation note: see the surrounding code for the behavior described here.
    dest_pdf = book.paths.root_dir / resolved_pdf.name
    if not dest_pdf.exists():
        print(f"[*] Kopiowanie PDF do katalogu ksiÄ…ĹĽki: {dest_pdf.name}")
        dest_pdf.write_bytes(resolved_pdf.read_bytes())

    print("[+] Struktura katalogĂłw ksiÄ…ĹĽki:")
    print(f"    - Root:  {book.paths.root_dir}")
    print(f"    - Scans: {book.paths.scans_dir}")
    print(f"    - Pages: {book.paths.pages_dir}")
    print(f"    - Audio: {book.paths.audio_dir}")
    print("-" * 70)

    # 2. Create domain job (ConversionJob)
    job = ConversionJob.create(book_slug=slug, pdf_path=resolved_pdf)

    # Implementation note: see the surrounding code for the behavior described here.
    use_case = default_container.create_convert_pdf_book_use_case()

    cmd = StartConversionCommand(
        pdf_path=resolved_pdf,
        book_slug=slug,
        dpi=dpi,
        start_page=start_page,
        end_page=end_page,
        scans_dir=book.paths.scans_dir,
        pages_dir=book.paths.pages_dir,
    )

    # 4. Execute conversion orchestration
    print("[*] RozpoczÄ™cie orkiestracji (ConvertPdfBookUseCase.execute)...")
    start_time = time.perf_counter()

    use_case.execute(cmd, job)

    elapsed = time.perf_counter() - start_time

    # Implementation note: see the surrounding code for the behavior described here.
    print("-" * 70)
    print(" PODSUMOWANIE KONWERSJI")
    print("-" * 70)
    print(f"Status zadania:        {job.state.value}")
    print(f"Przetworzone strony:   {job.completed_pages}")
    print(f"BĹ‚Ä™dne strony:         {len(job.failed_pages)}")
    print(f"ĹÄ…czny czas:           {elapsed:.2f} s")

    # Implementation note: see the surrounding code for the behavior described here.
    jpg_files = sorted(book.paths.scans_dir.glob("*.jpg"))
    md_files = sorted(book.paths.pages_dir.glob("*.md"))

    print(f"[+] Wygenerowane skany JPG w scans/:      {len(jpg_files)} plikĂłw")
    if jpg_files:
        sample_jpg = jpg_files[0]
        print(f"    Pierwszy skan: {sample_jpg.name} ({sample_jpg.stat().st_size / 1024:.1f} KB)")

    print(f"[+] Wygenerowane dokumenty w pages/:      {len(md_files)} plikĂłw")
    if md_files:
        sample_md = md_files[0]
        print(f"    Pierwszy dokument MD: {sample_md.name} ({sample_md.stat().st_size} bajtĂłw)")

    # Implementation note: see the surrounding code for the behavior described here.
    repo.set_active_book(str(slug))
    print(f"[+] KsiÄ…ĹĽka '{slug}' zostaĹ‚a ustawiona jako aktywna w magazynie (SSOT).")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="Potok konwersji ksiÄ…ĹĽki PDF na JPG i Markdown")
    parser.add_argument(
        "--pdf",
        type=str,
        default="data/books/pdf/Go/100-Go-Mistakes-and-How-to-Avoid-Them-(Teiva-Harsanyi)_bibis.ir.pdf",
        help="ĹšcieĹĽka do pliku PDF",
    )
    parser.add_argument(
        "--slug",
        type=str,
        default="100_go_mistakes",
        help="Unikalny identyfikator ksiÄ…ĹĽki (slug)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="100 Go Mistakes and How to Avoid Them",
        help="TytuĹ‚ ksiÄ…ĹĽki",
    )
    parser.add_argument(
        "--author",
        type=str,
        default="Teiva Harsanyi",
        help="Autor ksiÄ…ĹĽki",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="Pierwsza strona do konwersji (1-based)",
    )
    parser.add_argument(
        "--end-page",
        type=int,
        default=10,
        help="Ostatnia strona do konwersji (1-based)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="RozdzielczoĹ›Ä‡ renderowania skanĂłw JPG",
    )

    args = parser.parse_args()
    run_pipeline(
        pdf_path=Path(args.pdf),
        book_slug_raw=args.slug,
        title=args.title,
        author=args.author,
        start_page=args.start_page,
        end_page=args.end_page,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
