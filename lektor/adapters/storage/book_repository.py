"""Filesystem repository for managing books and metadata."""

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from ...application.ports.storage_ports import BookRepositoryProtocol
from ...domain.book_models import Book, BookMetadata, BookPaths
from ...domain.conversion_models import DocumentScan, create_page_number, to_book_slug


class FileSystemBookRepository(BookRepositoryProtocol):
    """Repository implementing BookRepositoryProtocol based on filesystem."""

    def __init__(self, books_dir: Path, default_active_slug: str = "cloud_native_go") -> None:
        self.books_dir = books_dir.resolve()
        self.default_active_slug = default_active_slug
        self.books_dir.mkdir(parents=True, exist_ok=True)

    def get_book(self, slug_or_title: str) -> Book | None:
        """Retrieves book metadata by slug."""
        clean_query = str(to_book_slug(slug_or_title))
        books = self.list_books()

        for b in books:
            if b.slug == clean_query or b.slug == slug_or_title:
                return b
            if b.title.lower() == slug_or_title.lower():
                return b
            if clean_query in b.slug or b.slug in clean_query:
                return b

        return None

    def list_books(self) -> Sequence[Book]:
        """Returns all discovered books in storage."""
        if not self.books_dir.exists():
            return []

        books: list[Book] = []
        for item in sorted(self.books_dir.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                book = self._load_book_from_dir(item)
                if book is not None:
                    books.append(book)

        return books

    def get_active_book(self) -> Book:
        """Returns currently active book in the repository."""
        if hasattr(self, "_active_slug") and self._active_slug:
            active = self.get_book(self._active_slug)
            if active is not None:
                return active

        active_file = self.books_dir / ".active"
        if active_file.exists():
            try:
                saved_slug = active_file.read_text(encoding="utf-8").strip()
                if saved_slug:
                    active = self.get_book(saved_slug)
                    if active is not None:
                        return active
            except Exception:
                pass

        active = self.get_book(self.default_active_slug)
        if active is not None:
            return active

        books = self.list_books()
        if not books:
            return self.create_book(
                title=self.default_active_slug.replace("_", " ").title(),
                slug=self.default_active_slug,
                author="Matthew Titmus",
                language="pl",
                description=f"Audiobook i opracowanie ksiÄ…ĹĽki {self.default_active_slug}.",
            )

        for b in books:
            if b.slug == self.default_active_slug:
                return b

        return books[0]

    def set_active_book(self, slug: str) -> Book:
        """Sets specified book as active."""
        book = self.get_book(slug)
        if book is None:
            book = self.create_book(title=slug.replace("_", " ").title(), slug=slug)
        self._active_slug = book.slug

        try:
            (self.books_dir / ".active").write_text(book.slug, encoding="utf-8")
        except Exception:
            pass

        return book

    def save_pdf(self, slug: str, filename: str, content: bytes) -> Path:
        """Saves binary PDF file into the book storage structure."""
        clean_slug = str(to_book_slug(slug))
        book_dir = self.books_dir / clean_slug
        book_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = book_dir / filename
        pdf_path.write_bytes(content)
        return pdf_path

    def get_existing_scans(self, slug: str) -> Sequence[DocumentScan]:
        """Returns list of existing rendered page scans (JPG)."""
        clean_slug = str(to_book_slug(slug))
        book = self.get_book(clean_slug)
        scans_dir = (
            book.paths.scans_dir
            if book
            else (self.books_dir / clean_slug / "scans")
        )
        if not scans_dir.exists():
            return ()

        scan_paths: dict[int, Path] = {}
        for p in scans_dir.glob("page_*.jpg"):
            m = re.search(r"page_(\d+)", p.name)
            if m and p.stat().st_size > 0:
                try:
                    p_num = int(m.group(1))
                    if p_num < 1:
                        continue
                    existing = scan_paths.get(p_num)
                    if existing is None or len(p.name) < len(existing.name):
                        scan_paths[p_num] = p
                except (ValueError, TypeError):
                    # Implementation note: see the surrounding code for the behavior described here.
                    continue
        scans = [
            DocumentScan(
                page_number=create_page_number(page_num),
                scan_path=scan_path,
                dpi=300,
            )
            for page_num, scan_path in scan_paths.items()
        ]
        return sorted(scans, key=lambda s: int(s.page_number))

    def pdf_exists(self, slug: str) -> bool:
        """Checks whether PDF file for given slug exists in storage."""
        book = self.get_book(slug)
        if book and book.paths.original_pdf and book.paths.original_pdf.exists():
            return True
        clean_slug = str(to_book_slug(slug))
        book_dir = self.books_dir / clean_slug
        if not book_dir.exists():
            return False
        return bool(list(book_dir.glob("*.pdf")))

    def get_book_stats(self, slug: str) -> tuple[int, int, int]:
        """Returns book page statistics: (total_pages, audio_pages, percent_done)."""
        book = self.get_book(slug)
        if book is None:
            return 0, 0, 0
        pages = len(list(book.paths.pages_dir.glob("*.md"))) if book.paths.pages_dir.exists() else 0
        audio = len(list(book.paths.audio_dir.glob("*.wav"))) if book.paths.audio_dir.exists() else 0
        scans = len(self.get_existing_scans(slug))
        return pages, audio, scans

    def save_metadata(self, slug: str, metadata: BookMetadata) -> None:
        """Persists book metadata to metadata.json in book directory."""
        target_dir = self.books_dir / slug
        target_dir.mkdir(parents=True, exist_ok=True)
        meta_file = target_dir / "metadata.json"

        data = asdict(metadata)
        meta_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def create_book(
        self,
        title: str,
        slug: str,
        author: str = "",
        language: str = "pl",
        description: str = "",
    ) -> Book:
        """Creates canonical structure of a new book in storage."""
        clean_slug = to_book_slug(slug) if slug else to_book_slug(title)
        book_dir = self.books_dir / clean_slug
        book_dir.mkdir(parents=True, exist_ok=True)

        pages_dir = book_dir / "pages"
        scans_dir = book_dir / "scans"
        images_dir = book_dir / "images"
        audio_dir = book_dir / "audio"

        pages_dir.mkdir(parents=True, exist_ok=True)
        scans_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)

        metadata = BookMetadata(
            title=title,
            slug=clean_slug,
            author=author,
            language=language,
            total_pages=0,
            description=description,
        )
        self.save_metadata(clean_slug, metadata)

        paths = BookPaths(
            root_dir=book_dir,
            pages_dir=pages_dir,
            scans_dir=scans_dir,
            images_dir=images_dir,
            audio_dir=audio_dir,
        )

        return Book(metadata=metadata, paths=paths)

    def _load_book_from_dir(self, book_dir: Path) -> Book | None:
        """Loads Book entity from directory without modifying disk state."""
        slug = book_dir.name
        meta_file = book_dir / "metadata.json"

        pages_dir = book_dir / "pages"
        scans_dir = book_dir / "scans"
        images_dir = book_dir / "images"
        audio_dir = book_dir / "audio"
        translated_dir = book_dir / "translated"

        pages_count = len(list(pages_dir.glob("*.md"))) if pages_dir.exists() else 0
        metadata = self._read_metadata(slug, meta_file, pages_count)
        original_pdf = self._find_original_pdf(book_dir, slug)

        paths = BookPaths(
            root_dir=book_dir,
            pages_dir=pages_dir,
            scans_dir=scans_dir,
            images_dir=images_dir,
            audio_dir=audio_dir,
            original_pdf=original_pdf,
            translated_dir=translated_dir if translated_dir.exists() else None,
        )

        return Book(metadata=metadata, paths=paths)

    def _read_metadata(self, slug: str, meta_file: Path, pages_count: int) -> BookMetadata:
        """Reads book metadata from metadata.json or generates defaults."""
        if meta_file.exists():
            try:
                raw_data = json.loads(meta_file.read_text(encoding="utf-8"))
                return BookMetadata(
                    title=str(raw_data.get("title", slug.replace("_", " ").title())),
                    slug=str(raw_data.get("slug", slug)),
                    author=str(raw_data.get("author", "")),
                    language=str(raw_data.get("language", "pl")),
                    total_pages=int(raw_data.get("total_pages", pages_count)),
                    description=str(raw_data.get("description", "")),
                    created_at=str(raw_data.get("created_at", "")),
                )
            except Exception:
                pass
        return BookMetadata(
            title=slug.replace("_", " ").title(),
            slug=slug,
            total_pages=pages_count,
        )

    @staticmethod
    def _find_original_pdf(book_dir: Path, slug: str = "") -> Path | None:
        """Searches for original book PDF file in its directory or data root."""
        # Implementation note: see the surrounding code for the behavior described here.
        pdf_files = list(book_dir.glob("*.pdf"))
        if pdf_files:
            return pdf_files[0]

        # Implementation note: see the surrounding code for the behavior described here.
        orig_dir = book_dir / "original"
        if orig_dir.exists():
            orig_pdf_files = list(orig_dir.glob("*.pdf"))
            if orig_pdf_files:
                return orig_pdf_files[0]

        # Implementation note: see the surrounding code for the behavior described here.
        pdf_library = book_dir.parent / "pdf"
        if pdf_library.exists() and slug:
            stop_words = {"with", "and", "the", "a", "an", "in", "of", "for", "to", "on"}
            slug_words = [w for w in slug.lower().split("_") if len(w) >= 3 and w not in stop_words]
            if slug_words:
                best_match: Path | None = None
                best_score = 0
                for candidate in pdf_library.rglob("*.pdf"):
                    c_name = candidate.name.lower()
                    score = sum(1 for w in slug_words if w in c_name)
                    min_req = min(2, len(slug_words))
                    if score >= min_req and score > best_score:
                        best_score = score
                        best_match = candidate
                if best_match:
                    return best_match

        return None
