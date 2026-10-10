# Deployment topology (level 4)

## Overview

The deployment diagram illustrates the physical deployment topology on a developer workstation running Windows with an NVIDIA GPU accelerator.

```mermaid
C4Deployment
    title Deployment Diagram - Local Hardware Execution Topology

    Deployment_Node(workstation, "Developer Workstation", "Windows 11 x64, 12 Cores, 32 GB RAM") {
        Deployment_Node(gpuHardware, "NVIDIA Graphics Card", "GeForce RTX 3060 12 GB VRAM") {
            Container(cudaCores, "CUDA Compute Engine", "v12.x Runtime", "Executes neural matrix calculations and tensor operations.")
        }

        Deployment_Node(pyRuntime, "Python Runtime Environment", "Python 3.14.x x64") {
            Container(fastapiProc, "FastAPI / Uvicorn Process", "PID: Main / Port 7860", "Hosts application server, GUI routers, background worker threads, and SSE emitter.")
            Container(forwarderProc, "TCP Port Forwarder Process", "PID: Forwarder / Port 80", "Asynchronously relays HTTP traffic from port 80 to 7860 via loopback.")
            Container(pytorchEngine, "PyTorch Engine", "In-Process DLLs", "Loads OmniVoice/Chatterbox TTS weights into GPU memory on demand.")
        }

        Deployment_Node(cppRuntime, "llama.cpp Runtime", "Win-x86_64 AVX2 CUDA 12 Binary") {
            Container(llamaProc, "llama-server.exe Process", "PID: Subprocess / Port 1234", "Hosts Gemma 4 12B GGUF with BF16 multimodal projection weights.")
        }

        Deployment_Node(storageDisk, "NVMe Solid State Drive", "NTFS File System") {
            ContainerDb(projectData, "Project Data Directory", "./data", "Contains books/, audio_book/, cache/, and configuration.")
        }

        Deployment_Node(clientBrowser, "Web Client Environment", "Google Chrome / Edge") {
            Container(browserUi, "Browser Execution Context", "Chromium Engine", "Executes audio player, UI controllers, and renders DOM elements.")
        }
    }

    Rel(browserUi, forwarderProc, "Requests direct access", "HTTP / Port 80")
    Rel(forwarderProc, fastapiProc, "Pipes TCP traffic", "TCP Loopback / Port 7860")
    Rel(browserUi, fastapiProc, "Requests assets, API, and SSE telemetry", "HTTP REST / Port 7860")
    Rel(fastapiProc, llamaProc, "Manages lifecycle via subprocess and sends inference requests", "HTTP / Port 1234")
    Rel(fastapiProc, pytorchEngine, "Invokes speech generation via Python API", "In-Process Call")
    Rel(pytorchEngine, cudaCores, "Allocates tensors (~2.5-3.5 GB VRAM)", "CUDA API")
    Rel(llamaProc, cudaCores, "Offloads 99 layers (~7.5-8.5 GB VRAM)", "CUDA Driver API")
    Rel(fastapiProc, projectData, "Persists WAV tracks, Markdown, and JSON metadata", "Win32 File I/O")

```

## Hardware and process allocation

* **FastAPI / Uvicorn process (port 7860)**: Core application process executing use cases, coordinating background threads with `threading.Thread`, and reading filesystem paths.
* **Port forwarder process (port 80)**: Enables local network access without explicit port specifications in the address bar.
* **Multimodal server subprocess (`llama-server.exe`, port 1234)**: Launched on demand by `ProcessModelHandle` when entering `SLOT_VISION`. It is cleanly terminated before speech synthesis begins.
* **PyTorch in-process engine**: Loaded by `PyTorchModelHandle` during `SLOT_AUDIO_TTS`. Memory is actively cleared via garbage collection and CUDA cache flush calls when the slot is released.
* **Single GPU constraint**: Because both models cannot simultaneously reside in 12 GB VRAM without out-of-memory errors, the deployment relies on hardware-level mutual exclusion.
ng.
