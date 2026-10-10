# Modele książki i ścieżek

## Przegląd

Dokument opisuje encje domenowe, obiekty wartości oraz silne typy reprezentujące książki, granice systemu plików i niezmienniki katalogu danych.

---

## 1. Silne typy identyfikatorów

```python
PageNumber = NewType("PageNumber", int)

```

Typ `PageNumber` zabezpiecza logikę przed przekazywaniem nieprawidłowych indeksów lub liczb ujemnych. Każda wartość przechodzi przez walidację w fabryce domenowej:

```python
def create_page_number(value: int) -> PageNumber:
    if value < 1:
        raise ValueError(f"Numer strony musi być >= 1, otrzymano: {value}")
    return PageNumber(value)

```

---

## 2. Obiekty wartości (Value Objects)

### `BookMetadata`

Niezmienny rekord przechowujący deskryptory katalogowe książki:

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

Hermetyzuje granice ścieżek dla konkretnej książki w strukturze `data/books/<slug>/`:

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

Centralne pojedyncze źródło prawdy (SSOT) dla ścieżek systemowych. Agreguje zasoby ogólnoaplikacyjne oraz dynamiczne powiązania aktywnej książki:

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

## 3. Korzeń agregatu: `Book`

Encja `Book` łączy metadane z fizycznym układem katalogów książki:

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