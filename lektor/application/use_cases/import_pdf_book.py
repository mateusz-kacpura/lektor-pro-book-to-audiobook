"""
lektor.application.use_cases.import_pdf_book
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use case: Importing a PDF file, creating book structure,
reading page count via PdfSplitterProtocol, and registering in the repository.
Strict typing without Any.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ...domain.book_models import Book, BookMetadata
from ...domain.conversion_models import to_book_slug, validate_book_slug
from ..ports.ocr_ports import PdfSplitterProtocol
from ..ports.storage_ports import BookRepositoryProtocol


@dataclass(frozen=True)
class ImportPdfBookCommand:
    """Command parameters for importing a PDF file."""
    file_bytes: bytes
    filename: str
    title: Optional[str] = None
    author: Optional[str] = None
    slug: Optional[str] = None


@dataclass(frozen=True)
class ImportPdfBookResult:
    """Result of importing a new PDF book."""
    book: Book
    pdf_path: Path
    total_pages: int


class ImportPdfBookUseCase:
    """
    Orchestrates PDF file import process into book storage.
    Guarantees encapsulation of disk persistence, slug calculation, and page discovery.
    """

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        pdf_splitter: PdfSplitterProtocol,
    ) -> None:
        self._book_repo = book_repository
        self._pdf_splitter = pdf_splitter

    def execute(self, cmd: ImportPdfBookCommand) -> ImportPdfBookResult:
        if not cmd.filename.lower().endswith(".pdf"):
            raise ValueError("Wymagany jest plik z rozszerzeniem .pdf")

        if not cmd.file_bytes:
            raise ValueError("PrzesĹ‚any plik PDF jest pusty (0 bajtĂłw).")

        stem = Path(cmd.filename).stem
        computed_title = (
            cmd.title.strip()
            if (cmd.title and cmd.title.strip())
            else stem.replace("_", " ").replace("-", " ").title()
        )

        if cmd.slug and cmd.slug.strip():
            clean_slug = validate_book_slug(cmd.slug.strip())
        else:
            clean_slug = to_book_slug(stem)

        # Implementation note: see the surrounding code for the behavior described here.
        book = self._book_repo.create_book(
            title=computed_title,
            slug=str(clean_slug),
            author=cmd.author.strip() if (cmd.author and cmd.author.strip()) else "",
            language="pl",
            description=f"Zaimportowano z pliku PDF: {cmd.filename}",
        )

        # Implementation note: see the surrounding code for the behavior described here.
        dest_pdf_path = self._book_repo.save_pdf(str(clean_slug), cmd.filename, cmd.file_bytes)

        # Implementation note: see the surrounding code for the behavior described here.
        try:
            total_pages = self._pdf_splitter.get_page_count(dest_pdf_path)
        except Exception:
            total_pages = 0

        # Implementation note: see the surrounding code for the behavior described here.
        updated_metadata = BookMetadata(
            title=computed_title,
            slug=str(clean_slug),
            author=cmd.author.strip() if (cmd.author and cmd.author.strip()) else "",
            language="pl",
            total_pages=total_pages,
            description=f"Zaimportowano z pliku PDF: {cmd.filename}",
        )
        self._book_repo.save_metadata(clean_slug, updated_metadata)

        # Implementation note: see the surrounding code for the behavior described here.
        refreshed_book = self._book_repo.get_book(clean_slug) or book

        return ImportPdfBookResult(
            book=refreshed_book,
            pdf_path=dest_pdf_path,
            total_pages=total_pages,
        )
