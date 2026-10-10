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
        break Gdy zgłoszono anulowanie zadania
            UC->>Sse: broadcast(CANCELLED)
        end

        UC->>Sse: broadcast(TRANSLATING, numer_strony, opis_kroku)
        
        alt Strona Markdown istnieje i skip_existing=True
            UC->>UC: job.mark_page_completed()
        else Pomyślna ekstrakcja wizyjna AI
            UC->>Vision: translate_scan(scan, custom_prompt)
            activate Vision
            Vision-->>UC: TranslatedMarkdownPage
            deactivate Vision
            UC->>Validator: validate_page_integrity(markdown)
            UC->>Repo: write_markdown(out_page_path, markdown)
            UC->>UC: job.mark_page_completed()
        else Błąd lub limit czasu (Timeout)
            UC->>UC: job.mark_page_failed(numer_strony, treść_błędu)
            UC->>Sse: broadcast(BŁĄD, treść_błędu)
        end

        UC->>Sse: broadcast(migawka telemetrii: tok/s, eta, vram)
    end

    UC->>Sse: broadcast(COMPLETED)
    deactivate UC
```

---

## 2. Kontrakt komendy wejściowej

Potok przyjmuje komendę `StartConversionCommand`:

| Pole | Typ | Opis |
| --- | --- | --- |
| `pdf_path` | `Path` | Ścieżka do pliku źródłowego PDF. |
| `book_slug` | `str` | Identyfikator książki w formacie kebab-case. |
| `dpi` | `int` | Rozdzielczość rasteryzacji skanów (domyślnie 300). |
| `page_range` | `tuple[int, int] \| None` | Zakres stron do przetworzenia lub `None` (całość). |
| `skip_existing` | `bool` | Pomija strony z istniejącym plikiem Markdown. |
| `custom_prompt` | `str \| None` | Opcjonalny prompt sterujący tłumaczeniem technicznym. |

---

## 3. Niezmienniki i odporność operacyjna

1. **Wywłaszczanie VRAM**: Przed wysłaniem zapytań do serwera wizyjnego przypadek użycia wywołuje `arbiter.acquire(SLOT_VISION)`. Gwarantuje to, że modele TTS nie zajmują pamięci karty graficznej.
2. **Spójność atomowa zapisu**: Strona trafia do repozytorium dopiero po pomyślnej walidacji przez `MarkdownPageValidationService`. Błędnie przetłumaczone pliki nie zastępują poprawnych danych.
3. **Płynna telemetria SSE**: Każdy krok emituje zdarzenia do `TelemetryBroadcasterProtocol`, zasilając pasek postępu w Web GUI bez blokowania wątku roboczego.
