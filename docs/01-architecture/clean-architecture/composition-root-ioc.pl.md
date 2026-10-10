# Punkt składania aplikacji i odwrócenie sterowania (IoC)

## Przegląd

Punkt składania aplikacji (ang. *composition root*) to wyznaczone miejsce w kodzie, w którym następuje powiązanie abstrakcji z konkretnymi implementacjami i inicjalizacja grafu zależności. W projekcie Lektor Pro rolę tę pełni klasa `ApplicationContainer` z modułu `lektor.infrastructure.container`.

```mermaid
classDiagram
    direction TB
    class ApplicationContainerProtocol {
        <<Protocol>>
        +get_book_repository() BookRepositoryProtocol
        +get_page_repository() PageRepositoryProtocol
        +get_tts_engine() TTSEngineProtocol
        +get_audio_stitcher() AudioStitcherProtocol
        +get_audio_cleaner() AudioCleanerProtocol
        +get_audio_cache() AudioCacheProtocol
        +get_model_arbiter() AIModelArbiterProtocol
        +get_pdf_splitter() PdfSplitterProtocol
        +get_vision_translator() VisionTranslatorProtocol
        +create_synthesize_page_use_case() SynthesizePageUseCase
        +create_convert_pdf_book_use_case() ConvertPdfBookUseCase
        +reset_book_context(new_paths) None
    }

    class ApplicationContainer {
        -_data_paths: DataPaths
        -_base_dir: Path
        -_book_repo: BookRepositoryProtocol
        -_tts_engine: TTSEngineProtocol
        -_model_arbiter: AIModelArbiterProtocol
        +reset_book_context() None
    }

    class CliEntrypoint {
        +main(args_list, container)
    }

    class GuiFactory {
        +create_app(container, gui_paths)
    }

    ApplicationContainerProtocol <|.. ApplicationContainer : implementuje
    ApplicationContainer ..> CliEntrypoint : wstrzykiwany do
    ApplicationContainer ..> GuiFactory : wstrzykiwany do

```

## Wzorzec składania zależności

Architektura systemu eliminuje ukryte singletony i niekontrolowany stan globalny poprzez jawne wstrzykiwanie zależności:

1. **Czyste kontrakty protokołów**: Warstwa aplikacji definiuje kontrakt `ApplicationContainerProtocol` w `lektor.application.ports.container_ports`. Ani przypadki użycia, ani adaptery interfejsów nie zależą od klas infrastrukturalnych.
2. **Cykl życia kontekstu książki**: Kontekst aktywnej książki może być przełączany w czasie działania programu bez konieczności restartu procesu. Wywołanie metody `reset_book_context` unieważnia instancje repozytoriów powiązanych z bieżącą książką (`_book_repo`, `_page_repo`, `_notes_repo`) i wiąże ścieżki z nowym katalogiem docelowym (`data/books/<slug>/`).
3. **Wstrzykiwanie w punktach wejścia**:
* **Konsola CLI (`main.py`)**: Przekazuje `default_container` bezpośrednio jako argument funkcji głównej: `lektor.adapters.cli.main.main(..., container=default_container)`.
* **Interfejs przeglądarkowy (`lektor.adapters.gui.app`)**: Zapisuje instancję kontenera w stanie aplikacji FastAPI (`app.state.container = container`). Routery pobierają serwisy za pośrednictwem mechanizmu `fastapi.Depends(get_container)`.

