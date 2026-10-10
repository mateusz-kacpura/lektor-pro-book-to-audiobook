"""
lektor.application.use_cases.switch_active_book
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use case for dynamically switching the active book (Business Rules 1, 2, 3).
Strict layer separation: zero dependencies on infrastructure/config (Dependency Rule).
"""

from ...domain.conversion_models import validate_book_slug
from ..dtos import BookMetadataDTO, SwitchActiveBookCommand
from ..ports.storage_ports import BookRepositoryProtocol


class SwitchActiveBookUseCase:
    """Use case responsible for switching the active book context."""

    def __init__(self, book_repo: BookRepositoryProtocol) -> None:
        self._repo = book_repo

    def execute(self, cmd: SwitchActiveBookCommand) -> BookMetadataDTO:
        slug = validate_book_slug(str(cmd.slug))

        # Implementation note: see the surrounding code for the behavior described here.
        book_opt = self._repo.get_book(str(slug))
        if book_opt is None:
            book_opt = self._repo.create_book(
                title=str(slug).replace("_", " ").title(),
                slug=str(slug),
            )

        # Implementation note: see the surrounding code for the behavior described here.
        active_book = self._repo.set_active_book(str(slug))

        # Implementation note: see the surrounding code for the behavior described here.
        pages, audio, scans = self._repo.get_book_stats(str(slug))

        return BookMetadataDTO(
            slug=str(slug),
            title=active_book.title,
            total_pages=pages,
            audio_pages=audio,
            scan_pages=scans,
            is_active=True,
        )
