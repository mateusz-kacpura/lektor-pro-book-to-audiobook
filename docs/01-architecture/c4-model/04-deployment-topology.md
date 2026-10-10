# Deployment topology (level 4)

## Overview

The deployment diagram illustrates the physical deployment topology on a developer workstation running Windows with an NVIDIA GPU accelerator.

```mermaid
flowchart TB
    classDef hardware fill:#2d3748,stroke:#1a202c,color:#fff,stroke-width:2px;
    classDef process fill:#1168bd,stroke:#0b4884,color:#fff,stroke-width:2px;
    classDef runtime fill:#4361ee,stroke:#3a0ca3,color:#fff,stroke-width:2px;
    classDef storage fill:#5a6268,stroke:#343a40,color:#fff,stroke-width:2px;
    classDef client fill:#08427b,stroke:#073b6f,color:#fff,stroke-width:2px;

    subgraph Workstation [" 🖥️ Developer Workstation (Windows 11 x64, 12 Cores, 32 GB RAM) "]
        direction TB

        subgraph ClientGroup [" Client Execution Environment "]
            browserUi["🌐 <b>Browser Execution Context</b><br/><i>[Google Chrome / Microsoft Edge]</i><br/><br/>Audio player, UI controllers, and DOM rendering."]:::client
        end

        subgraph HostNetworking [" Host Networking & Application Server "]
            forwarderProc["🔀 <b>TCP Port Forwarder Process</b><br/><i>[Python 3.14 / asyncio / Port 80]</i><br/><br/>Asynchronously relays port 80 traffic to 7860."]:::process
            fastapiProc["⚡ <b>FastAPI / Uvicorn Process</b><br/><i>[Python 3.14 x64 / Port 7860]</i><br/><br/>Hosts REST server, GUI routers, worker threads, SSE emitter."]:::process
        end

        subgraph PythonEnv [" Python Runtime & In-Process TTS "]
            pytorchEngine["🎙️ <b>PyTorch Engine</b><br/><i>[In-Process DLLs inside FastAPI]</i><br/><br/>Loads OmniVoice/Chatterbox TTS weights into VRAM on demand."]:::runtime
        end

        subgraph LlamaEnv [" llama.cpp Runtime (Subprocess) "]
            llamaProc["🧠 <b>llama-server.exe Process</b><br/><i>[Win-x86_64 AVX2 CUDA 12 Binary / Port 1234]</i><br/><br/>Hosts Gemma 4 12B GGUF with BF16 visual projector."]:::process
        end

        subgraph HardwareGroup [" Physical Hardware & Storage "]
            direction LR
            cudaCores["⚡ <b>NVIDIA GeForce RTX 3060 (12 GB VRAM)</b><br/><i>[CUDA 12.x Runtime / Tensor Cores]</i><br/><br/>Sequential preemption: VLM inference (~8 GB) or TTS (~3 GB)."]:::hardware
            projectData[("💾 <b>NVMe Solid State Drive (NTFS)</b><br/><i>[Project Data Directory ./data]</i><br/><br/>Contains books/, audio_book/, cache/, and .env config.")]:::storage
        end
    end

    browserUi -->|"Direct access request<br/><b>[HTTP / Port 80]</b>"| forwarderProc
    browserUi -->|"Fetches assets & REST API<br/><b>[HTTP REST / SSE / Port 7860]</b>"| fastapiProc
    forwarderProc -->|"Pipes TCP traffic<br/><b>[127.0.0.1:7860]</b>"| fastapiProc

    fastapiProc -->|"Lifecycle & inference requests<br/><b>[Subprocess / HTTP 1234]</b>"| llamaProc
    fastapiProc -->|"Invokes speech generation<br/><b>[In-Process Call]</b>"| pytorchEngine
    fastapiProc -->|"Persists WAV tracks, Markdown, metadata<br/><b>[Win32 File I/O]</b>"| projectData

    pytorchEngine -->|"Allocates TTS tensors in VRAM (~3 GB)<br/><b>[CUDA API]</b>"| cudaCores
    llamaProc -->|"Offloads layers in VRAM (~8 GB)<br/><b>[CUDA Driver API]</b>"| cudaCores
```

## Hardware and process allocation

* **FastAPI / Uvicorn process (port 7860)**: Core application process executing use cases, coordinating background threads with `threading.Thread`, and reading filesystem paths.
* **Port forwarder process (port 80)**: Enables local network access without explicit port specifications in the address bar.
* **Multimodal server subprocess (`llama-server.exe`, port 1234)**: Launched on demand by `ProcessModelHandle` when entering `SLOT_VISION`. It is cleanly terminated before speech synthesis begins.
* **PyTorch in-process engine**: Loaded by `PyTorchModelHandle` during `SLOT_AUDIO_TTS`. Memory is actively cleared via garbage collection and CUDA cache flush calls when the slot is released.
* **Single GPU constraint**: Because both models cannot simultaneously reside in 12 GB VRAM without out-of-memory errors, the deployment relies on hardware-level mutual exclusion.
