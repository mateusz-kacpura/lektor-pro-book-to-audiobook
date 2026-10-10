# Routery FastAPI i specyfikacja DTO

## Przegląd

Warstwa API interfejsu przeglądarkowego (`lektor.adapters.gui.routers`) udostępnia punkty końcowe podzielone na moduły funkcjonalne. Tłumaczy żądania HTTP na obiekty komend warstwy aplikacji oraz serializuje odpowiedzi domenowe do modeli Pydantic.

---

## 1. Wykaz routerów

```text
lektor/adapters/gui/routers/
├── converter.py    # Podział PDF, ekstrakcja wizyjna, renderowanie skanów, strumień SSE
├── generator.py    # Synteza pojedynczych stron i zadań wsadowych, zatrzymywanie
├── player.py       # Strumieniowanie nagrań, obsługa nagłówków zakresu, playlista
├── studio.py       # Synteza fragmentów tekstu, historia nagrań studia, usuwanie WAV
├── notes.py        # Zapis i odczyt notatek czytelnika
├── books.py        # Rejestr książek, zmiana aktywnej pozycji, metadane
└── web.py          # Serwowanie zasobów statycznych i szablonów HTML

```

---

## 2. Modele transferu danych (Pydantic DTO)

Zdefiniowane w module `lektor.adapters.gui.dtos`:

### `StartConversionRequest`

```python
class StartConversionRequest(BaseModel):
    book_slug: str
    pdf_path: Optional[str] = None
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    dpi: int = Field(default=300, ge=72, le=600)
    custom_prompt: Optional[str] = None
    skip_existing: bool = True

```

### `SynthesizePageRequest`

```python
class SynthesizePageRequest(BaseModel):
    page_id: str
    skip_existing: bool = False
    save_normalized_text: bool = True
    audio_format: Literal["wav", "mp3"] = "wav"

```

### `SynthesizeSnippetRequest`

```python
class SynthesizeSnippetRequest(BaseModel):
    markdown: str
    snippet_id: Optional[str] = None
    language_mode: Literal["bilingual", "pl", "en"] = "bilingual"
    force: bool = False

```

---

## 3. Obsługa nagłówków zakresu (`/audio/{slug}/{track}`)

Router odtwarzacza obsługuje żądania z nagłówkiem `Range: bytes=start-end`, zwracając odpowiedź ze statusem `206 Partial Content`. Umożliwia to natychmiastowe przewijanie nagrań lektora w przeglądarce bez konieczności pobierania całego pliku dźwiękowego.