# Porty i protokoły podsystemu OCR i analizy wizyjnej

## Przegląd

Dokument definiuje kontrakty portów odpowiedzialnych za rasteryzację dokumentów, formatowanie Markdownu, komunikację z API modeli multimodalnych oraz orkiestrację tłumaczenia wizyjnego. Zdefiniowane w module `lektor.application.ports.ocr_ports`.

---

## 1. `PdfSplitterProtocol`

Izoluje logikę biznesową od silników renderowania plików PDF:

```python
class PdfSplitterProtocol(Protocol):
    def split_pdf(
        self,
        pdf_path: Path,
        output_dir: Path,
        dpi: int = 300,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
    ) -> Sequence[DocumentScan]:
        """Dzieli plik PDF na sekwencyjne obrazy stron w formacie JPEG."""
        ...

    def get_page_count(self, pdf_path: Path) -> int:
        """Zwraca łączną liczbę stron w dokumencie PDF."""
        ...

    def render_page(
        self,
        pdf_path: Path,
        page_index_0based: int,
        output_path: Path,
        dpi: int = 300,
    ) -> None:
        """Renderuje pojedynczą stronę o indeksie 0-based do pliku graficznego."""
        ...

```

---

## 2. `VisionApiClientProtocol` i `VisionApiResponse`

Określa kontrakt klienta HTTP komunikującego się z serwerami kompatybilnymi z API OpenAI:

```python
@dataclass(frozen=True)
class VisionApiResponse:
    raw_content: str
    tokens_per_sec: float
    total_tokens: int
    duration_sec: float

class VisionApiClientProtocol(Protocol):
    @property
    def model_name(self) -> str:
        """Nazwa lub identyfikator aktywnego modelu wizyjnego."""
        ...

    def send_vision_request(
        self,
        image_bytes: bytes,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> VisionApiResponse:
        """Wysyła obraz oraz prompty, zwracając ustrukturyzowaną odpowiedź z metrykami."""
        ...

```

---

## 3. `VisionPromptBuilderProtocol`

Odpowiada za konstruowanie zapytań dla modeli tłumaczących:

```python
class VisionPromptBuilderProtocol(Protocol):
    def build_system_prompt(self) -> str:
        """Tworzy systemowy prompt definiujący rolę inżyniera i tłumacza technicznego."""
        ...

    def build_user_prompt(self, custom_instructions: Optional[str] = None) -> str:
        """Tworzy zapytanie użytkownika z poleceniem ochrony kodu i diagramów."""
        ...

```

---

## 4. `VisionTranslatorProtocol`

Orkiestruje proces analizy obrazu, ekstrakcji kodu i generowania diagramów:

```python
class VisionTranslatorProtocol(Protocol):
    def translate_scan(
        self,
        scan: DocumentScan,
        custom_prompt: Optional[str] = None,
    ) -> TranslatedMarkdownPage:
        """Analizuje skan strony, tłumaczy narrację i zwraca domenową stronę Markdown."""
        ...

```

## 5. `BookMarkdownFormatterProtocol`

Wzbogaca surowy tekst o nagłówek metadanych w formacie JSON oraz stopkę odsyłającą do skanu:

```python
class BookMarkdownFormatterProtocol(Protocol):
    def format_markdown(
        self,
        raw_md: str,
        page_num: PageNumber,
        img_name: str,
        book_dir_name: str = "scans",
    ) -> str:
        """Formatuje tekst Markdown, dodając blok komentarza JSON i odnośnik do obrazu."""
        ...

```