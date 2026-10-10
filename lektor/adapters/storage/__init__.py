"""Storage and persistence adapters."""

from .book_repository import FileSystemBookRepository
from .file_repository import FileSystemPageRepository
from .notes_repository import FileSystemNotesRepository
from .studio_repository import FileSystemStudioHistoryRepository

__all__ = [
    "FileSystemBookRepository",
    "FileSystemNotesRepository",
    "FileSystemPageRepository",
    "FileSystemStudioHistoryRepository",
]