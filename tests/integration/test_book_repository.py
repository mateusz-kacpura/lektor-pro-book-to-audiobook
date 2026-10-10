"""
Testy jednostkowe uniwersalnego magazynu książek (FileSystemBookRepository).
Weryfikacja Single Source of Truth (SSOT), pobierania po tytułach,
slugach oraz struktury kanonicznych folderów.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from lektor.adapters.storage.book_repository import FileSystemBookRepository
from lektor.domain.book_models import BookMetadata


class TestBookRepository(unittest.TestCase):
    """Testy repozytorium książek."""

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo = FileSystemBookRepository(books_dir=self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_and_get_book(self) -> None:
        book = self.repo.create_book(
            title="Clean Architecture with Python",
            slug="clean_architecture_python",
            author="Sam Keen",
            language="pl",
            description="Książka o czystej architekturze"
        )
        self.assertEqual(book.title, "Clean Architecture with Python")
        self.assertEqual(book.slug, "clean_architecture_python")
        self.assertTrue(book.paths.pages_dir.exists())
        self.assertTrue(book.paths.scans_dir.exists())
        self.assertTrue(book.paths.images_dir.exists())
        self.assertTrue(book.paths.audio_dir.exists())

        # Pobieranie po slug
        found = self.repo.get_book("clean_architecture_python")
        self.assertIsNotNone(found)
        if found is not None:
            self.assertEqual(found.metadata.author, "Sam Keen")

        # Pobieranie po tytule
        found_by_title = self.repo.get_book("Clean Architecture with Python")
        self.assertIsNotNone(found_by_title)

    def test_list_books(self) -> None:
        self.repo.create_book(title="Book One", slug="book_one")
        self.repo.create_book(title="Book Two", slug="book_two")

        books = self.repo.list_books()
        self.assertEqual(len(books), 2)
        slugs = [b.slug for b in books]
        self.assertIn("book_one", slugs)
        self.assertIn("book_two", slugs)

    def test_save_and_reload_metadata(self) -> None:
        _ = self.repo.create_book(title="Test Book", slug="test_book")
        new_meta = BookMetadata(
            title="Updated Title",
            slug="test_book",
            author="New Author",
            language="en",
            total_pages=42,
            description="Nowy opis"
        )
        self.repo.save_metadata("test_book", new_meta)

        reloaded = self.repo.get_book("test_book")
        self.assertIsNotNone(reloaded)
        if reloaded is not None:
            self.assertEqual(reloaded.metadata.title, "Updated Title")
            self.assertEqual(reloaded.metadata.total_pages, 42)
            self.assertEqual(reloaded.metadata.author, "New Author")


if __name__ == "__main__":
    unittest.main()
