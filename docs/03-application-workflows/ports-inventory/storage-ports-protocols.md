# Storage ports & protocols

## Overview

This document specifies repository port contracts for persistent document access, book catalog management, markdown scratchpad notes, and studio synthesis history. Defined in `lektor.application.ports.storage_ports` conforming strictly to the interface segregation principle (ISP).

---

## 1. Segregated page repository contracts

Allows components to depend strictly on narrow reader, writer, or inspector responsibilities:

```python
class PageContentReaderProtocol(Protocol):
    def read_markdown(self, path: Path) -> str:
        """Reads Markdown file contents in UTF-8 encoding."""
        ...

    def list_pages(self, directory: Path, pattern: str = "*.md") -> Sequence[Path]:
        """Discovers and numerically sorts Markdown page files."""
        ...

    def page_exists(self, path: Path, min_bytes: int = 0) -> bool:
        """Verifies if a page file exists and exceeds byte threshold."""
        ...

    def get_page_size(self, path: Path) -> int:
        """Returns page file size in bytes."""
        ...

class PageContentWriterProtocol(Protocol):
    def write_markdown(self, path: Path, content: str) -> None:
        """Writes Markdown content creating parent directories as needed."""
        ...

    def save_preview(self, path: Path, text: str) -> None:
        """Saves text normalization preview file."""
        ...

    def save_state(self, path: Path, state_dict: dict[str, object] | SynthesisStats) -> None:
        """Persists processing state metadata to JSON file."""
        ...

class PageMediaInspectorProtocol(Protocol):
    def audio_exists(self, path: Path, min_bytes: int = 1000) -> bool:
        """Verifies if an audio track exists with stable size."""
        ...

class PageRepositoryProtocol(
    PageContentReaderProtocol,
    PageContentWriterProtocol,
    PageMediaInspectorProtocol,
    Protocol,
):
    """Aggregated contract representing complete page repository operations."""
    ...

```

---

## 2. Segregated book catalog contracts

```python
class BookReaderProtocol(Protocol):
    def get_book(self, slug_or_title: str) -> Book | None:
        """Retrieves a book by unique slug or exact title."""
        ...

    def list_books(self) -> Sequence[Book]:
        """Returns all registered books in the catalog."""
        ...

    def get_active_book(self) -> Book:
        """Returns the currently active book entity."""
        ...

    def get_book_stats(self, slug: str) -> tuple[int, int, int]:
        """Returns tuple of (total_markdown_pages, audio_pages, scan_pages)."""
        ...

    def get_existing_scans(self, slug: str) -> Sequence[DocumentScan]:
        """Discovers existing high-resolution page bitmaps."""
        ...

    def pdf_exists(self, slug: str) -> bool:
        """Verifies if an original source PDF file exists for the book."""
        ...

class BookWriterProtocol(Protocol):
    def set_active_book(self, slug: str) -> Book:
        """Sets the specified book slug as active and updates marker file."""
        ...

    def save_metadata(self, slug: str, metadata: BookMetadata) -> None:
        """Persists book metadata descriptors to metadata.json."""
        ...

    def create_book(
        self,
        title: str,
        slug: str,
        author: str = "",
        language: str = "pl",
        description: str = "",
    ) -> Book:
        """Creates canonical workspace directory tree for a new book."""
        ...

    def save_pdf(self, slug: str, filename: str, content: bytes) -> Path:
        """Stores binary PDF file content inside book root."""
        ...

class BookRepositoryProtocol(BookReaderProtocol, BookWriterProtocol, Protocol):
    """Aggregated Single Source of Truth book catalog repository interface."""
    ...

```

---

## 3. Peripheral repository protocols

```python
class NotesRepositoryProtocol(Protocol):
    def get_note(self, note_id: str) -> str:
        """Retrieves note Markdown content by identifier."""
        ...

    def save_note(self, note_id: str, content: str) -> Path:
        """Persists note Markdown content to disk."""
        ...

class StudioHistoryRepositoryProtocol(Protocol):
    def get_history(self) -> Sequence[StudioItem]:
        """Retrieves saved studio recordings verified against disk."""
        ...

    def save_history(self, items: Sequence[StudioItem | dict[str, object]]) -> None:
        """Persists recordings metadata list to JSON storage."""
        ...

    def add_or_update_item(self, item: StudioItem | dict[str, object]) -> None:
        """Prepends or updates an item in the recordings history."""
        ...

    def delete_item(self, item_id: str) -> bool:
        """Removes history record and deletes associated audio file from disk."""
        ...

```