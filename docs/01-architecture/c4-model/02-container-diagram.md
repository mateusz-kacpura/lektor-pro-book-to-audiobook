

### Plik 3: `docs/01-architecture/c4-model/02-container-diagram.md` (Wersja angielska)

Zapisz w: `docs/01-architecture/c4-model/02-container-diagram.md`

```mar# Container diagram (level 2)

## Overview

The container diagram illustrates the runtime boundaries, technologies, and inter-process communication mechanisms comprising Lektor Pro.

```mermaid
C4Container
    title Container Diagram - Lektor Pro

    Person(user, "User", "Accesses the application via web browser or terminal.")

    System_Boundary(c1, "Lektor Pro Environment") {
        Container(browser, "Web GUI Frontend", "Vanilla JavaScript (ES Modules), HTML5 Audio, CSS3", "In-browser single-page workspace with player, Markdown reader, note scratchpad, and telemetry.")
        Container(cli, "CLI Interface", "Python 3.14 / argparse", "Command-line tools for batch audio synthesis, book catalog management, and scan conversion.")
        Container(webServer, "Application Server", "Python 3.14 / FastAPI & Uvicorn", "Provides REST endpoints, Server-Sent Events telemetry, static resource routing, and dependency injection.")
        Container(portFwd, "TCP Port Forwarder", "Python 3.14 / asyncio", "Pipes port 80 traffic to internal port 7860 for direct LAN and Tailscale access.")
        Container(appCore, "Clean Core & Use Cases", "Python 3.14 (Strict Typing, No Any)", "Domain models, linguistic normalizers, conversion workflows, and port contracts.")
        Container(audioEngine, "Audio DSP & TTS Subsystem", "NumPy, SciPy, SoundFile, PyTorch, Silero VAD", "Speech synthesis, zero-allocation buffering, noise filtering, and SHA-256 caching.")
        Container(vramArbiter, "Dynamic VRAM Arbiter", "Python subprocess / PyTorch CUDA API", "Enforces mutual exclusion on the GPU, preempting llama-server before loading TTS engines.")
    }

    ContainerDb(fs, "Local Data Storage", "File System", "Stores data/books/<slug>/, pages, scans, audio WAV files, and .env configuration.")
    Container_Ext(llamaServer, "Multimodal VLM Server", "llama-server.exe (C++ / CUDA)", "Hosts Google Gemma 4 or Qwen models with mmproj visual projectors on port 1234.")

    Rel(user, browser, "Operates player, triggers batch conversions, writes notes", "HTTP / Web Browser")
    Rel(user, cli, "Runs batch generation or checks catalog status", "Terminal / Shell")
    Rel(browser, webServer, "Invokes REST endpoints, uploads files, listens to live progress", "HTTP REST / SSE")
    Rel(user, portFwd, "Connects via port 80", "TCP")
    Rel(portFwd, webServer, "Forwards client traffic to 7860", "TCP Loopback")
    Rel(cli, appCore, "Invokes use cases directly using container", "Direct method calls")
    Rel(webServer, appCore, "Dispatches HTTP requests to use cases via container dependencies", "FastAPI Depends")
    Rel(appCore, audioEngine, "Requests speech synthesis, stitcher concatenation, and audio cleaning", "Audio ports")
    Rel(appCore, vramArbiter, "Acquires model slots (SLOT_VISION or SLOT_AUDIO_TTS)", "Resource ports")
    Rel(appCore, fs, "Reads and writes book pages, states, and metadata", "Storage ports / File I/O")
    Rel(vramArbiter, llamaServer, "Starts, monitors, and terminates server process via signals and taskkill", "Subprocess / HTTP health check")
    Rel(appCore, llamaServer, "Sends page images for translation and diagram extraction", "HTTP REST / Port 1234")

```

## Runtime containers

1. **Web GUI frontend**: Built with native modern JavaScript (ES modules) and styled with CSS custom properties. It manages audio playback, time scrubbing, and window management without single-page application framework overhead.
2. **Application server (FastAPI)**: Serves assets, coordinates background workers with `threading.Thread`, and streams conversion metrics via `SseTelemetryBroadcasterAdapter`.
3. **TCP port forwarder**: A lightweight `asyncio` loop enabling access on standard HTTP port 80 alongside the primary port 7860.
4. **Clean core and use cases**: Domain services and application interactors with strict type checking, relying on port abstractions.
5. **Audio DSP and TTS subsystem**: Combines neural speech generation with digital signal processing (DSP) filters and content-addressable storage.
6. **Dynamic VRAM arbiter**: Coordinates execution between VLM processes and in-process PyTorch models on memory-constrained GPUs.
Persists markdown, audio, and state", "File I/O")

```

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

```ng.
