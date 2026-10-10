# Porty i protokoły magazynów danych

## Przegląd

Dokument zawiera specyfikację kontraktów repozytoriów dla operacji na plikach stron, katalogu książek, notatkach oraz historii studia nagrań. Zdefiniowane w module `lektor.application.ports.storage_ports` z zachowaniem zasady segregacji interfejsów (ISP).

---

## 1. Wydzielone kontrakty repozytorium stron

Pozwalają komponentom zależnym wymagać wyłącznie wąskich interfejsów odczytu, zapisu lub inspekcji plików:

```python
class PageContentReaderProtocol(Protocol):
    def read_markdown(self, path: Path) -> str:
        """Odczytuje zawartość pliku Markdown w kodowaniu UTF-8."""
        ...

    def list_pages(self, directory: Path, pattern: str = "*.md") -> Sequence[Path]:
        """Wyszukuje i sortuje numerycznie pliki stron Markdown."""
        ...

    def page_exists(self, path: Path, min_bytes: int = 0) -> bool:
        """Sprawdza, czy plik strony Markdown istnieje i ma wymagany rozmiar."""
        ...

    def get_page_size(self, path: Path) -> int:
        """Zwraca rozmiar pliku strony w bajtach."""
        ...

class PageContentWriterProtocol(Protocol):
    def write_markdown(self, path: Path, content: str) -> None:
        """Zapisuje zawartość do pliku Markdown, tworząc katalogi nadrzędne."""
        ...

    def save_preview(self, path: Path, text: str) -> None:
        """Zapisuje plik podglądu znormalizowanego tekstu."""
        ...

    def save_state(self, path: Path, state_dict: dict[str, object] | SynthesisStats) -> None:
        """Zapisuje metadane stanu przetwarzania w formacie JSON."""
        ...

class PageMediaInspectorProtocol(Protocol):
    def audio_exists(self, path: Path, min_bytes: int = 1000) -> bool:
        """Sprawdza, czy plik dźwiękowy istnieje i ma stabilny rozmiar."""
        ...

class PageRepositoryProtocol(
    PageContentReaderProtocol,
    PageContentWriterProtocol,
    PageMediaInspectorProtocol,
    Protocol,
):
    """Zagregowany kontrakt pełnego repozytorium plików stron."""
    ...

```

---

## 2. Wydzielone kontrakty katalogu książek

```python
class BookReaderProtocol(Protocol):
    def get_book(self, slug_or_title: str) -> Book | None:
        """Pobiera książkę po identyfikatorze (slug) lub dokładnym tytule."""
        ...

    def list_books(self) -> Sequence[Book]:
        """Zwraca listę wszystkich zarejestrowanych książek w magazynie."""
        ...

    def get_active_book(self) -> Book:
        """Zwraca aktualnie aktywną książkę."""
        ...

    def get_book_stats(self, slug: str) -> tuple[int, int, int]:
        """Zwraca krotkę (liczba_stron_md, liczba_nagran_audio, liczba_skanow)."""
        ...

    def get_existing_scans(self, slug: str) -> Sequence[DocumentScan]:
        """Zwraca listę istniejących gotowych skanów stron w formacie JPEG."""
        ...

    def pdf_exists(self, slug: str) -> bool:
        """Sprawdza, czy plik PDF dla danej książki istnieje w magazynie."""
        ...

class BookWriterProtocol(Protocol):
    def set_active_book(self, slug: str) -> Book:
        """Ustawia wskazaną książkę jako aktywną i zapisuje znacznik na dysku."""
        ...

    def save_metadata(self, slug: str, metadata: BookMetadata) -> None:
        """Zapisuje metadane książki w pliku metadata.json."""
        ...

    def create_book(
        self,
        title: str,
        slug: str,
        author: str = "",
        language: str = "pl",
        description: str = "",
    ) -> Book:
        """Tworzy kanoniczną strukturę katalogów nowej książki w magazynie."""
        ...

    def save_pdf(self, slug: str, filename: str, content: bytes) -> Path:
        """Zapisuje binarny plik PDF w katalogu głównym książki."""
        ...

class BookRepositoryProtocol(BookReaderProtocol, BookWriterProtocol, Protocol):
    """Zagregowany kontrakt repozytorium książek (pojedyncze źródło prawdy)."""
    ...

```

---

## 3. Protokoły repozytoriów pomocniczych

```python
class NotesRepositoryProtocol(Protocol):
    def get_note(self, note_id: str) -> str:
        """Pobiera treść notatki o zadanym identyfikatorze."""
        ...

    def save_note(self, note_id: str, content: str) -> Path:
        """Zapisuje treść notatki i zwraca ścieżkę do pliku."""
        ...

class StudioHistoryRepositoryProtocol(Protocol):
    def get_history(self) -> Sequence[StudioItem]:
        """Pobiera listę wpisów historii nagrań zweryfikowanych z dyskiem."""
        ...

    def save_history(self, items: Sequence[StudioItem | dict[str, object]]) -> None:
        """Zapisuje listę historii nagrań do pliku JSON."""
        ...

    def add_or_update_item(self, item: StudioItem | dict[str, object]) -> None:
        """Dodaje lub aktualizuje wpis w historii nagrań na początku listy."""
        ...

    def delete_item(self, item_id: str) -> bool:
        """Usuwa wpis z historii oraz powiązany plik dźwiękowy z dysku."""
        ...

```