# Przypadek użycia: tłumaczenie i ekstrakcja wizyjna AI

## Przegląd

Przypadek użycia `ConvertPdfBookUseCase` (`lektor.application.use_cases.convert_pdf_book`) koordynuje multimodalny potok konwersji: rasteryzację dokumentu, weryfikację skanów, inferencję modelu wizyjnego, ochronę kodu oraz emisję telemetrii w czasie rzeczywistym.

---

## 1. Przebieg potoku wykonawczego

```mermaid
sequenceDiagram
    autonumber
    participant Worker as Wątek w tle
    participant UC as ConvertPdfBookUseCase
    participant Arbiter as AIModelArbiterProtocol
    participant Splitter as PdfSplitterProtocol
    participant Vision as VisionTranslatorProtocol
    participant Validator as MarkdownPageValidationService
    participant Repo as PageRepositoryProtocol
    participant Sse as TelemetryBroadcasterProtocol

    Worker->>UC: execute(StartConversionCommand, job)
    activate UC
    
    UC->>Arbiter: acquire(SLOT_VISION)
    
    alt Skany JPEG istnieją już na dysku
        UC->>UC: Ponowne użycie skanów (Pominięcie renderowania)
    else Brakujące skany w katalogu
        UC->>Splitter: split_pdf(dpi=300)
    end

    loop Dla każdej strony dokumentu
        alt Zgłoszono anulowanie zadania
            UC->>Sse: broadcast(CANCELLED)
            break
        end

        UC->>Sse: broadcast(TRANSLATING, numer_strony, opis_kroku)
        
        alt Strona Markdown istnieje i skip_existing=True
            UC->>UC: job.mark_page_completed()
        else Uruchomienie ekstrakcji multimodalnej
            try
                UC->>Vision: translate_scan(scan, custom_prompt)
                activate Vision
                Vision-->>UC: TranslatedMarkdownPage
                deactivate Vision
                UC->>Validator: validate_page_integrity(markdown)
                UC->>Repo: write_markdown(out_page_path, markdown)
                UC->>UC: job.mark_page_completed()
            catch Błąd / Timeout
                UC->>UC: job.mark_page_failed(numer_strony, treść_błędu)
                UC->>Sse: broadcast(BŁĄD, treść_błędu)
            end
        end

        UC->>Sse: broadcast(migawka telemetrii: tok/s, eta, vram)
    end

    UC->>Sse: broadcast(COMPLETED)
    deactivate UC

```

---

## 2. Kontrakt komendy wejściowej

```python
@dataclass(frozen=True)
class StartConversionCommand:
    pdf_path: Path
    book_slug: BookSlug
    dpi: int = 300
    custom_prompt: Optional[str] = None
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    skip_existing: bool = True
    scans_dir: Optional[Path] = None
    pages_dir: Optional[Path] = None

```

---

## 3. Niezmienniki i odporność operacyjna

* **Optymalizacja skanów**: Jeśli pliki JPEG w 300 DPI znajdują się w katalogu `scans/`, kosztowny etap podziału PDF jest pomijany, a zadanie przechodzi od razu do inferencji modelu.
* **Odporność na błędy (`BR-013`)**: Błąd analizy strony $K$ trafia do rejestru `job.failed_pages`, po czym potok bezpiecznie przechodzi do strony $K+1$.
* **Precyzja telemetrii (`BR-014`)**: Każda strona odpytuje `GpuTelemetryProtocol`, na bieżąco wyliczając prędkość tokenów na sekundę oraz przewidywany czas do końca (ETA).
