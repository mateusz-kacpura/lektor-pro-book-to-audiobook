# Container diagram (level 2)

## Overview

The container diagram illustrates the runtime boundaries, technologies, and inter-process communication mechanisms comprising Lektor Pro.

```mermaid
flowchart TB
    classDef person fill:#08427b,stroke:#073b6f,color:#fff,stroke-width:2px;
    classDef container fill:#1168bd,stroke:#0b4884,color:#fff,stroke-width:2px;
    classDef storage fill:#5a6268,stroke:#343a40,color:#fff,stroke-width:2px;
    classDef extProcess fill:#6c757d,stroke:#495057,color:#fff,stroke-width:2px;

    user["👤 <b>User / Reader</b><br/><i>[Person]</i><br/><br/>Accesses the application via web browser or terminal."]:::person

    subgraph LektorEnv [" 🏛️ Lektor Pro Runtime Environment "]
        direction TB

        subgraph IngressGroup [" Client Entrypoints "]
            direction LR
            browser["🌐 <b>Web GUI Frontend</b><br/><i>[Vanilla JS, ESM, HTML5 Audio, CSS3]</i><br/><br/>Single-page desktop workspace with audio player,<br/>Markdown reader, note scratchpad, and SSE telemetry."]:::container
            cli["💻 <b>CLI Interface</b><br/><i>[Python 3.14 / argparse]</i><br/><br/>Command-line tools for batch audio synthesis,<br/>book catalog management, and scan conversion."]:::container
            portFwd["🔀 <b>TCP Port Forwarder</b><br/><i>[Python 3.14 / asyncio]</i><br/><br/>Relays port 80 traffic to internal port 7860<br/>for direct LAN and Tailscale access."]:::container
        end

        webServer["⚡ <b>Application Server</b><br/><i>[Python 3.14 / FastAPI & Uvicorn]</i><br/><br/>Provides REST endpoints, Server-Sent Events telemetry,<br/>static resource routing, and dependency injection."]:::container

        appCore["⚙️ <b>Clean Core & Use Cases</b><br/><i>[Python 3.14 (Strict Typing, No Any)]</i><br/><br/>Domain models, linguistic normalizers,<br/>conversion workflows, and port contracts."]:::container

        subgraph ProcessingGroup [" Audio & Hardware Resource Subsystems "]
            direction LR
            audioEngine["🎵 <b>Audio DSP & TTS Subsystem</b><br/><i>[NumPy, SciPy, SoundFile, PyTorch, Silero VAD]</i><br/><br/>Speech synthesis, zero-allocation buffering,<br/>noise filtering, and SHA-256 audio caching."]:::container
            vramArbiter["🛡️ <b>Dynamic VRAM Arbiter</b><br/><i>[Python subprocess / PyTorch CUDA API]</i><br/><br/>Enforces mutual exclusion on the GPU,<br/>preempting llama-server before loading TTS."]:::container
        end
    end

    subgraph ExternalGroup [" Storage & External Processes "]
        direction LR
        fs[("💾 <b>Local Data Storage</b><br/><i>[Host File System]</i><br/><br/>Stores data/books/<slug>/, pages, scans,<br/>audio WAV files, and .env configuration.")]:::storage
        llamaServer["🧠 <b>Multimodal VLM Server</b><br/><i>[llama-server.exe (C++ / CUDA)]</i><br/><br/>Hosts Google Gemma 4 or Qwen models with<br/>mmproj visual projectors on port 1234."]:::extProcess
    end

    user -->|"Operates Web UI<br/><b>[HTTP]</b>"| browser
    user -->|"Runs batch generation<br/><b>[CLI Shell]</b>"| cli
    user -->|"Connects via port 80<br/><b>[TCP:80]</b>"| portFwd

    portFwd -->|"Pipes traffic to 7860<br/><b>[TCP Loopback]</b>"| webServer
    browser -->|"Invokes REST endpoints & listens to SSE<br/><b>[HTTP REST / SSE]</b>"| webServer
    cli -->|"Invokes use cases directly<br/><b>[In-Memory Calls]</b>"| appCore
    webServer -->|"Dispatches requests to use cases<br/><b>[FastAPI Depends]</b>"| appCore

    appCore -->|"Requests speech synthesis & DSP cleaning<br/><b>[Audio Ports]</b>"| audioEngine
    appCore -->|"Acquires model slots (SLOT_VISION / SLOT_AUDIO_TTS)<br/><b>[Resource Ports]</b>"| vramArbiter
    appCore -->|"Reads and writes book pages, states, metadata<br/><b>[Storage Ports / File I/O]</b>"| fs
    appCore -->|"Sends page images for translation<br/><b>[HTTP REST / Port 1234]</b>"| llamaServer

    vramArbiter -.->|"Starts, monitors, and terminates server<br/><b>[Subprocess / Signals]</b>"| llamaServer
```

## Runtime containers

1. **Web GUI frontend**: Built with native modern JavaScript (ES modules) and styled with CSS custom properties. It manages audio playback, time scrubbing, and window management without single-page application framework overhead.
2. **Application server (FastAPI)**: Serves assets, coordinates background workers with `threading.Thread`, and streams conversion metrics via `SseTelemetryBroadcasterAdapter`.
3. **TCP port forwarder**: A lightweight `asyncio` loop enabling access on standard HTTP port 80 alongside the primary port 7860.
4. **Clean core and use cases**: Domain services and application interactors with strict type checking, relying on port abstractions.
5. **Audio DSP and TTS subsystem**: Combines neural speech generation with digital signal processing (DSP) filters and content-addressable storage.
6. **Dynamic VRAM arbiter**: Coordinates execution between VLM processes and in-process PyTorch models on memory-constrained GPUs.

---

## ⚙️ Container Specifications

| Container | Technology Stack | Network / Interface | Primary Responsibility |
| --- | --- | --- | --- |
| **Web GUI Frontend** | Vanilla JS (ESM), CSS3, HTML5 | In-browser DOM | Serves the window manager, audio player, markdown viewer, and real-time SSE listener. |
| **Port Forwarder** | Python `asyncio` (`port_forwarder.py`) | TCP `0.0.0.0:80` $\to$ `127.0.0.1:7860` | Allows seamless LAN access without specifying custom port numbers in mobile browsers. |
| **API & Application Server** | FastAPI, Uvicorn, Python 3.14 | HTTP `127.0.0.1:7860` | Exposes REST endpoints, validates Pydantic schemas, and manages worker threads (`JobExecutionManager`). |
| **CLI Runner** | Python `argparse` (`main.py`) | Standard CLI | Executes batch conversion and synthesis pipelines in headless automated environments. |
| **VRAM Resource Arbiter** | Python (`DynamicVramModelArbiter`) | Internal Protocol | Coordinates hardware preemption to prevent out-of-memory errors on consumer GPUs. |
| **Vision Model Runtime** | `llama-server.exe` (CUDA 12) | HTTP `127.0.0.1:1234/v1` | Performs multimodal vision OCR and technical translation into Polish Markdown. |
| **TTS & DSP Engine** | PyTorch, SciPy, NumPy, SoundFile | In-process CUDA / CPU | Synthesizes speech, cleans audio tails via Silero VAD, and normalizes output volume. |
| **File System Repository** | Host OS Filesystem | Directory Hierarchy | Canonical storage holding metadata, 300 DPI scans, generated markdown files, and audio tracks. |
