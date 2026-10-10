# Component diagrams (level 3)

## Overview

The component view details the internal decomposition of the application core, demonstrating strict compliance with clean architecture layer boundaries.

```mermaid
flowchart TB
    classDef adapter fill:#08427b,stroke:#073b6f,color:#fff,stroke-width:2px;
    classDef usecase fill:#1168bd,stroke:#0b4884,color:#fff,stroke-width:2px;
    classDef domain fill:#1f7a8c,stroke:#14525e,color:#fff,stroke-width:2px;
    classDef gateway fill:#5a6268,stroke:#343a40,color:#fff,stroke-width:2px;

    subgraph DrivingAdapters [" 🌐 Ingress Adapters (Driving / Entrypoints) "]
        direction LR
        guiRouters["⚡ <b>FastAPI Routers</b><br/><i>[Web GUI REST / SSE DTOs]</i>"]:::adapter
        cliMain["💻 <b>CLI Entry Point</b><br/><i>[lektor.adapters.cli.main]</i>"]:::adapter
    end

    subgraph AppLayer [" ⚙️ Application Use Cases Layer "]
        direction LR
        ucConvert["📄 <b>ConvertPdfBookUseCase</b><br/><i>[PDF Conversion Orchestrator]</i>"]:::usecase
        ucSynthPage["🎙️ <b>SynthesizePageUseCase</b><br/><i>[Page Synthesis Orchestrator]</i>"]:::usecase
        ucBatchSynth["📦 <b>BatchSynthesisUseCase</b><br/><i>[Batch Runner]</i>"]:::usecase
        ucStatus["📊 <b>GetBookStatusUseCase</b><br/><i>[Status Aggregator]</i>"]:::usecase
    end

    subgraph DomainLayer [" 🏛️ Domain Entities & Rules Layer "]
        direction TB
        normalizer["🔤 <b>TextNormalizationService</b><br/><i>[Text normalization & Go phonetics]</i>"]:::domain
        validator["🛡️ <b>MarkdownPageValidationService</b><br/><i>[Integrity validation & Mermaid checks]</i>"]:::domain
        glossary["📚 <b>TechnicalGlossaryService</b><br/><i>[Cloud Native term protection]</i>"]:::domain
        entities["🧱 <b>Domain Models & VOs</b><br/><i>[Book, ConversionJob, SpeechSegment, DataPaths]</i>"]:::domain
    end

    subgraph DrivenAdapters [" 🔌 Infrastructure & Driven Adapters "]
        direction TB
        pageRepo["💾 <b>FileSystemPageRepository</b><br/><i>[PageRepositoryProtocol]</i>"]:::gateway
        bookRepo["📁 <b>FileSystemBookRepository</b><br/><i>[BookRepositoryProtocol]</i>"]:::gateway
        universalTTS["🗣️ <b>UniversalTTSEngine</b><br/><i>[TTSEngineProtocol: OmniVoice / Chatterbox]</i>"]:::gateway
        audioCleaner["🧹 <b>SileroAudioCleaner</b><br/><i>[AudioCleanerProtocol: VAD & filters]</i>"]:::gateway
        audioStitcher["🪡 <b>NumpyAudioStitcher</b><br/><i>[AudioStitcherProtocol: WAV normalization]</i>"]:::gateway
        visionAdapter["👁️ <b>UniversalVisionTranslatorAdapter</b><br/><i>[VisionTranslatorProtocol: OpenAI API]</i>"]:::gateway
        pdfSplitter["📑 <b>PyMuPdfSplitterAdapter</b><br/><i>[PdfSplitterProtocol: 300 DPI JPEG]</i>"]:::gateway
        arbiter["⚖️ <b>DynamicVramModelArbiter</b><br/><i>[AIModelArbiterProtocol: VRAM preemption]</i>"]:::gateway
    end

    guiRouters -->|"Invokes via DTO"| ucConvert
    guiRouters -->|"Invokes via DTO"| ucSynthPage
    guiRouters -->|"Invokes via DTO"| ucStatus
    cliMain -->|"Invokes via DTO"| ucSynthPage
    cliMain -->|"Invokes via DTO"| ucBatchSynth
    ucBatchSynth -->|"Loops over pages"| ucSynthPage

    ucConvert -->|"Splits PDF pages"| pdfSplitter
    ucConvert -->|"Translates scans"| visionAdapter
    ucConvert -->|"Preempts GPU"| arbiter
    ucConvert -->|"Saves pages"| pageRepo
    ucConvert -->|"Validates content"| validator
    ucConvert -->|"Protects terms"| glossary

    ucSynthPage -->|"Segments speech"| normalizer
    ucSynthPage -->|"Synthesizes audio"| universalTTS
    ucSynthPage -->|"Stitches WAV buffers"| audioStitcher
    ucSynthPage -->|"Reads/writes state"| pageRepo
    ucSynthPage -->|"Leases VRAM"| arbiter

    universalTTS -->|"Cleans speech audio"| audioCleaner
    normalizer -->|"Constructs instances"| entities
    bookRepo -->|"Builds models"| entities
```

## Layer boundary analysis

* **Domain layer**: Contains entities, value objects, and domain services. It has zero external dependencies on third-party frameworks.
* **Application layer**: Defines ports as abstract protocols (`typing.Protocol`) and orchestrates use cases through command and query objects (DTOs).
* **Interface adapters layer**: Converts low-level payloads from HTTP, CLI, file systems, and hardware drivers into domain and application structures.
