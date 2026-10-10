# Przypadek użycia: import i podział dokumentu PDF

## Przegląd

Przypadki użycia z grupy importu i rasteryzacji odpowiadają za przyjęcie pliku PDF oraz jego podział na obrazy stron. Koordynowane przez `ImportPdfBookUseCase` (`lektor.application.use_cases.import_pdf_book`), `RenderPdfScansUseCase` oraz `RenderPdfScansStreamUseCase`, interaktory te przygotowują materiał do analizy wizyjnej.

---

## 1. Dekompozycja potoku przetwarzania

```mermaid
flowchart TD
    PDF[Plik PDF użytkownika] --> Import[ImportPdfBookUseCase]
    Import --> CreateBook[Utworzenie encji książki w repozytorium]
    Import --> SavePDF[Zapis binarnego PDF w katalogu książki]
    Import --> PageCount[Odczyt liczby stron przez PdfSplitterProtocol]
    Import --> Metadata[Aktualizacja pliku metadata.json]
    
    Metadata --> SplitChoice{Wybór trybu renderowania}
    SplitChoice -->|Synchroniczny batch| RenderSync[RenderPdfScansUseCase]
    SplitChoice -->|Strumień SSE na żywo| RenderStream[RenderPdfScansStreamUseCase]
    
    RenderSync --> Scans[Generowanie JPEG 300 DPI w scans/]
    RenderStream --> SSE[Emisja zdarzeń postępu do przeglądarki]
    RenderStream --> Scans

```

---

## 2. Kontrakty danych wejściowych i wyjściowych

### Komendy i struktury wynikowe

```python
@dataclass(frozen=True)
class ImportPdfBookCommand:
    file_bytes: bytes
    filename: str
    title: Optional[str] = None
    author: Optional[str] = None
    slug: Optional[str] = None

@dataclass(frozen=True)
class ImportPdfBookResult:
    book: Book
    pdf_path: Path
    total_pages: int

@dataclass(frozen=True)
class RenderScansCommand:
    book_slug: str
    dpi: int = 300
    start_page: Optional[int] = None
    end_page: Optional[int] = None

@dataclass(frozen=True)
class RenderScansStreamCommand:
    book_slug: str
    dpi: int = 300
    start_page: Optional[int] = None
    end_page: Optional[int] = None

```

---

## 3. Mechanizm strumieniowania rasteryzacji

W klasie `RenderPdfScansStreamUseCase` renderowanie obciążające procesor jest delegowane do osobnych wątków za pomocą `asyncio.to_thread`, co zapobiega blokowaniu asynchronicznej pętli zdarzeń serwera:

```python
async def execute_stream(self, cmd: RenderScansStreamCommand) -> AsyncIterator[dict[str, object]]:
    # 1. Weryfikacja książki i obecności pliku PDF
    # 2. Obliczenie zakresu stron [start_page, end_page]
    # 3. Emisja zdarzenia rozpoczęcia (started)
    for idx in range(start_idx, end_idx):
        file_name, _ = await asyncio.to_thread(_render_page_worker, idx, page_1based)
        yield {
            "status": "rendering",
            "current_page": page_1based,
            "percent": pct,
            "file_name": file_name,
            "eta_sec": eta,
        }
    # 4. Emisja zdarzenia zakończenia (completed)

```