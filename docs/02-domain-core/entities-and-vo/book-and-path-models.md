# Book and path models

## Overview

This specification details the domain entities and value objects representing books, filesystem boundaries, and strong types encapsulating catalog invariants.

---

## 1. Strong identity types

```python
PageNumber = NewType("PageNumber", int)

```

The `PageNumber` type prevents accidental arithmetic errors or negative indexing. It is validated strictly using the domain factory:

```python
def create_page_number(value: int) -> PageNumber:
    if value < 1:
        raise ValueError(f"Page number must be >= 1, received: {value}")
    return PageNumber(value)

```

---

## 2. Value objects

### `BookMetadata`

Immutable record carrying catalog descriptors:

```python
@dataclass(frozen=True)
class BookMetadata:
    title: str
    slug: str
    author: str = ""
    language: str = "pl"
    total_pages: int = 0
    description: str = ""
    created_at: str = ""

```

### `BookPaths`

Encapsulates directory boundaries for an individual book under `data/books/<slug>/`:

```python
@dataclass(frozen=True)
class BookPaths:
    root_dir: Path
    pages_dir: Path
    scans_dir: Path
    images_dir: Path
    audio_dir: Path
    original_pdf: Path | None = None
    translated_dir: Path | None = None

```

### `DataPaths`

System-wide Single Source of Truth (SSOT) managing both global application assets and dynamic bindings for the currently active book:

```python
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

```

---

## 3. Aggregate root: `Book`

The `Book` entity combines descriptive metadata with filesystem layout:

```python
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

```