"""
lektor.application.use_cases.render_pdf_scans
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use case: Rendering PDF pages into JPG scans (300 DPI).
Strict typing without Any.
"""

from ...domain.conversion_models import validate_book_slug
from ..dtos import RenderScansCommand, RenderScansResultDTO
from ..ports.ocr_ports import PdfSplitterProtocol
from ..ports.storage_ports import BookRepositoryProtocol


class RenderPdfScansUseCase:
    """
    Use case responsible for synchronously rendering PDF scans
    for the selected book and saving to the scans/ directory.
    """

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        pdf_splitter: PdfSplitterProtocol,
    ) -> None:
        self._book_repo = book_repository
        self._pdf_splitter = pdf_splitter

    def execute(self, cmd: RenderScansCommand) -> RenderScansResultDTO:
        clean_slug = validate_book_slug(cmd.book_slug)
        book = self._book_repo.get_book(clean_slug)
        if not book:
            raise ValueError(f"Książka '{clean_slug}' nie istnieje.")

        pdf_file = book.paths.original_pdf
        if not pdf_file or not pdf_file.exists():
            for candidate in book.paths.root_dir.glob("*.pdf"):
                pdf_file = candidate
                break

        if not pdf_file or not pdf_file.exists():
            raise FileNotFoundError("W katalogu książki nie znaleziono pliku PDF.")

        book.paths.scans_dir.mkdir(parents=True, exist_ok=True)
        scans = self._pdf_splitter.split_pdf(
            pdf_path=pdf_file,
            output_dir=book.paths.scans_dir,
            dpi=cmd.dpi,
            start_page=cmd.start_page,
            end_page=cmd.end_page,
        )

        total_scans = len(self._book_repo.get_existing_scans(str(clean_slug)))
        return RenderScansResultDTO(
            book_slug=str(clean_slug),
            scans_created=len(scans),
            scans_dir=str(book.paths.scans_dir),
            total_scans=total_scans,
            message=f"Pomyślnie wyrenderowano {len(scans)} skanów w {cmd.dpi} DPI dla książki '{clean_slug}'.",
        )
