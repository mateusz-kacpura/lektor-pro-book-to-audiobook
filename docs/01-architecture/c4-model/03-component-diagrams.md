# Component diagrams (level 3)

## Overview

The component view details the internal decomposition of the application core, demonstrating strict compliance with clean architecture layer boundaries.

```mermaid
C4Component
    title Component Diagram - Application Core & Interface Adapters

    Container_Boundary(adapters, "Interface Adapters Layer") {
        Component(guiRouters, "FastAPI Routers", "converter, generator, player, studio, notes, web", "Maps HTTP payloads to application command DTOs.")
        Component(cliMain, "CLI Entry Point", "lektor.adapters.cli.main", "Parses command line arguments and drives use cases.")
        Component(bookRepo, "FileSystemBookRepository", "BookRepositoryProtocol", "Manages book metadata, paths, scans, and page discovery.")
        Component(pageRepo, "FileSystemPageRepository", "PageRepositoryProtocol", "Performs filesystem read and write operations for Markdown and states.")
        Component(audioCleaner, "SileroAudioCleaner", "AudioCleanerProtocol", "Applies high-pass Butterworth filtering, Silero VAD boundary trimming, and cosine fades.")
        Component(audioStitcher, "NumpyAudioStitcher", "AudioStitcherProtocol", "Concatenates PCM arrays, normalizes volume, and saves WAV files.")
        Component(universalTTS, "UniversalTTSEngine", "TTSEngineProtocol", "Coordinates OmniVoice and Chatterbox backends.")
        Component(visionAdapter, "UniversalVisionTranslatorAdapter", "VisionTranslatorProtocol", "Encodes images, calls OpenAI-compatible API, and creates domain pages.")
        Component(pdfSplitter, "PyMuPdfSplitterAdapter", "PdfSplitterProtocol", "Renders PDF pages to 300 DPI JPEG bitmaps.")
        Component(arbiter, "DynamicVramModelArbiter", "AIModelArbiterProtocol", "Enforces preemption between vision server and PyTorch TTS.")
    }

    Container_Boundary(app, "Application Use Cases Layer") {
        Component(ucConvert, "ConvertPdfBookUseCase", "Orchestrator", "Coordinates PDF rendering, AI vision translation, validation, and progress broadcasting.")
        Component(ucSynthPage, "SynthesizePageUseCase", "Orchestrator", "Coordinates normalization, TTS generation, audio stitching, and state persistence.")
        Component(ucBatchSynth, "BatchSynthesisUseCase", "Batch Runner", "Iterates through book pages and executes page synthesis use case.")
        Component(ucStatus, "GetBookStatusUseCase", "Status Aggregator", "Aggregates overall completion metrics, durations, and page statuses.")
    }

    Container_Boundary(domain, "Domain Entities Layer") {
        Component(normalizer, "TextNormalizationService", "Domain Service", "Splits text, normalizes numbers, translates Go syntax, and applies phonetics.")
        Component(validator, "MarkdownPageValidationService", "Domain Service", "Validates Markdown integrity, code blocks, and Mermaid diagrams.")
        Component(glossary, "TechnicalGlossaryService", "Domain Service", "Protects Cloud Native terminology during LLM processing.")
        Component(entities, "Domain Models & VOs", "Book, ConversionJob, SpeechSegment, DataPaths", "Immutable domain state, invariants, and state machines.")
    }

    Rel(guiRouters, ucConvert, "Invokes via command DTO")
    Rel(guiRouters, ucSynthPage, "Invokes via command DTO")
    Rel(guiRouters, ucStatus, "Invokes via query DTO")
    Rel(cliMain, ucSynthPage, "Invokes via command DTO")
    Rel(cliMain, ucBatchSynth, "Invokes via command DTO")

    Rel(ucConvert, pdfSplitter, "Splits document")
    Rel(ucConvert, visionAdapter, "Translates page bitmap")
    Rel(ucConvert, arbiter, "Acquires SLOT_VISION")
    Rel(ucConvert, pageRepo, "Saves Markdown")
    Rel(ucConvert, validator, "Validates integrity")
    Rel(ucConvert, glossary, "Protects technical terms")

    Rel(ucSynthPage, normalizer, "Produces speech segments")
    Rel(ucSynthPage, universalTTS, "Synthesizes audio")
    Rel(ucSynthPage, audioStitcher, "Stitches segments")
    Rel(ucSynthPage, pageRepo, "Reads and writes page state")
    Rel(ucSynthPage, arbiter, "Acquires SLOT_AUDIO_TTS")

    Rel(universalTTS, audioCleaner, "Cleans audio tails")
    Rel(normalizer, entities, "Builds SpeechSegment instances")
    Rel(bookRepo, entities, "Builds Book entities and DataPaths")

```

## Layer boundary analysis

* **Domain layer**: Contains entities, value objects, and domain services. It has zero external dependencies on third-party frameworks.
* **Application layer**: Defines ports as abstract protocols (`typing.Protocol`) and orchestrates use cases through command and query objects (DTOs).
* **Interface adapters layer**: Converts low-level payloads from HTTP, CLI, file systems, and hardware drivers into domain and application structures.
