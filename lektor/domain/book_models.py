"""
lektor.domain.book_models
~~~~~~~~~~~~~~~~~~~~~~~~~
Entities and Value Objects representing a book and its filesystem structure.
Strict typing without Any.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import NewType

PageNumber = NewType("PageNumber", int)

def create_page_number(value: int) -> PageNumber:
    """Creates a validated page number (must be a positive integer)."""
    if value < 1:
        raise ValueError(f"Numer strony musi być >= 1, otrzymano: {value}")
    return PageNumber(value)

@dataclass(frozen=True)
class BookPageMetadata:
    title: str
    page_number: PageNumber
    original_file: str
    scan_file: str


@dataclass(frozen=True)
class BookMetadata:
    title: str
    slug: str
    author: str = ""
    language: str = "pl"
    total_pages: int = 0
    description: str = ""
    created_at: str = ""


@dataclass(frozen=True)
class BookPaths:
    root_dir: Path
    pages_dir: Path
    scans_dir: Path
    images_dir: Path
    audio_dir: Path
    original_pdf: Path | None = None
    translated_dir: Path | None = None


@dataclass(frozen=True)
class DataPaths:
    data_dir: Path
    books_dir: Path
    audio_dir: Path
    pages_dir: Path
    scans_dir: Path
    notes_dir: Path
    cache_dir: Path
    default_voice_path: Path
    images_dir: Path
    studio_audio_dir: Path
    studio_history_file: Path
    active_book_slug: str


@dataclass
class Book:
    metadata: BookMetadata
    paths: BookPaths

    @property
    def title(self) -> str:
        return self.metadata.title

    @property
    def slug(self) -> str:
        return self.metadata.slug