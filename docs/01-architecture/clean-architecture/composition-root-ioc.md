# Composition root & inversion of control

## Overview

The composition root is the centralized location where dependencies are resolved and instantiated. In Lektor Pro, this responsibility belongs to `ApplicationContainer`, located in `lektor.infrastructure.container`.

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

    ApplicationContainerProtocol <|.. ApplicationContainer : implements
    ApplicationContainer ..> CliEntrypoint : injected into
    ApplicationContainer ..> GuiFactory : injected into

```

## Composition pattern

Lektor Pro avoids hidden singletons and ambient global state by adopting explicit dependency injection:

1. **Pure protocol contracts**: The application layer defines `ApplicationContainerProtocol` in `lektor.application.ports.container_ports`. Neither use cases nor interface adapters depend on concrete infrastructure classes.
2. **Context-aware lifecycle**: The active book context can be switched dynamically at runtime without restarting the process. Calling `reset_book_context` clears cached repositories (`_book_repo`, `_page_repo`, `_notes_repo`) and rebinds paths to the target book directory (`data/books/<slug>/`).
3. **Dual entry-point injection**:
* **CLI (`main.py`)**: Passes `default_container` directly to `lektor.adapters.cli.main.main(..., container=default_container)`.
* **Web GUI (`lektor.adapters.gui.app`)**: Binds the container into FastAPI application state via `app.state.container = container`. Route handlers resolve components cleanly through `fastapi.Depends(get_container)`.

