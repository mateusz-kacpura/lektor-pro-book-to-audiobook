# Dependency rule enforcement

## Overview

The dependency rule is the foundational invariant of clean architecture: source code dependencies must point exclusively inward toward higher-level policies. Inner layers know nothing about outer layers.

```mermaid
flowchart TD
    subgraph Infrastructure["Frameworks & Drivers (Infrastructure)"]
        Config["config.py"]
        Container["container.py"]
        LlamaProc["llama-server.exe"]
    end

    subgraph Adapters["Interface Adapters"]
        Routers["FastAPI Routers"]
        CLI["CLI Commands"]
        Repos["FileSystem Repositories"]
        Engines["UniversalTTSEngine / PyMuPDF"]
        Arbiter["DynamicVramModelArbiter"]
    end

    subgraph Application["Application Layer (Use Cases & Ports)"]
        UC["Use Cases (Convert, Synthesize)"]
        Ports["Protocols (Audio, Storage, OCR)"]
        DTOs["Commands & Results (Data Transfer Objects)"]
    end

    subgraph Domain["Domain Layer (Entities & Rules)"]
        Entities["Entities (Book, ConversionJob)"]
        VO["Value Objects (SpeechSegment, DataPaths)"]
        Services["Domain Services (Normalizer, Glossary)"]
    end

    Infrastructure --> Adapters
    Adapters --> Application
    Application --> Domain

    style Domain fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc
    style Application fill:#0f172a,stroke:#818cf8,stroke-width:2px,color:#f8fafc
    style Adapters fill:#111827,stroke:#34d399,stroke-width:2px,color:#f8fafc
    style Infrastructure fill:#030712,stroke:#f43f5e,stroke-width:2px,color:#f8fafc

```

## Layer boundary definitions

| Layer | Directory | Permitted dependencies | Strictly forbidden dependencies |
| --- | --- | --- | --- |
| **Domain** | `lektor/domain/` | Python standard library only | Any external library, frameworks, filesystem I/O, network, application, adapters, infrastructure |
| **Application** | `lektor/application/` | `lektor/domain/`, Python standard library | Web frameworks (`fastapi`), machine learning frameworks (`torch`), I/O adapters, infrastructure |
| **Interface Adapters** | `lektor/adapters/` | `lektor/application/`, `lektor/domain/`, specialized I/O drivers (`pymupdf`, `soundfile`, `scipy`) | `lektor/infrastructure/` (no outward coupling) |
| **Frameworks & Drivers** | `lektor/infrastructure/` | `lektor/adapters/`, `lektor/application/`, `lektor/domain/` | None (outermost wiring layer) |

## Automated architecture validation

Compliance with the dependency rule is verified automatically in the CI pipeline using `import-linter`. The contract defined in `.importlinter` ensures that prohibited import paths fail static analysis:

```ini
[importlinter]
root_package = lektor

[importlinter:contract:clean-architecture-layers]
name = Clean Architecture Layer Dependencies
type = layers
layers =
    lektor.infrastructure
    lektor.adapters
    lektor.application
    lektor.domain
containers =
    lektor
```