"""
lektor.application.use_cases.list_books
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use case for retrieving list of all available books in storage.
Strict separation of layers: zero dependencies on infrastructure/config (Dependency Rule & ISP).
"""

from typing import Sequence

from ..dtos import BookMetadataDTO
from ..ports.storage_ports import BookReaderProtocol


class ListBooksUseCase:
    """Returns list of all books in storage with statistics and active book indicator."""

    def __init__(self, book_repo: BookReaderProtocol) -> None:
        self._repo = book_repo

    def execute(self) -> Sequence[BookMetadataDTO]:
        books = self._repo.list_books()
        active_book = self._repo.get_active_book()
        active_slug = active_book.slug if active_book else ""
        result: list[BookMetadataDTO] = []

        for book in books:
            slug = book.slug
            is_active = (slug == active_slug)
            pages, audio, scans = self._repo.get_book_stats(slug)

            result.append(
                BookMetadataDTO(
                    slug=slug,
                    title=book.title,
                    total_pages=pages,
                    audio_pages=audio,
                    scan_pages=scans,
                    is_active=is_active,
                )
            )

        return result
