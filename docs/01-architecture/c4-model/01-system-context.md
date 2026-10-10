# System context (level 1)

## Overview

The system context diagram shows the high-level boundary of the Lektor Pro application, the primary users, and external integrations. Lektor Pro operates locally on workstation hardware, providing end-to-end processing from raw technical book scans to synthesized speech audio.

```mermaid
flowchart TB
    classDef person fill:#08427b,stroke:#073b6f,color:#fff,stroke-width:2px;
    classDef internalSystem fill:#1168bd,stroke:#0b4884,color:#fff,stroke-width:2px;
    classDef externalSystem fill:#5a6268,stroke:#343a40,color:#fff,stroke-width:2px;

    user["👤 <b>Software Engineer / Reader</b><br/><i>[Person]</i><br/><br/>Listens to audiobooks, studies technical text,<br/>reads code listings, and architecture diagrams."]:::person
    
    lektor["🏛️ <b>Lektor Pro Platform</b><br/><i>[Software System]</i><br/><br/>Local orchestration system converting books (PDF/scans)<br/>to Markdown, generating speech audio,<br/>and providing a web player and Markdown studio."]:::internalSystem

    subgraph ExternalBoundary [" External Systems and Hardware Resources "]
        direction LR
        visionServer["🧠 <b>Local Multimodal AI Engine</b><br/><i>[External System]</i><br/><br/>Local LLM/VLM process (llama-server with Gemma 4<br/>or Qwen2.5-VL via OpenAI-compatible API)."]:::externalSystem
        filesystem[("💾 <b>Host File System</b><br/><i>[Storage / File I/O]</i><br/><br/>Local disk storage: PDF files, scanned images,<br/>generated Markdown pages, and PCM WAV buffers.")]:::externalSystem
        cuda["⚡ <b>NVIDIA CUDA Hardware</b><br/><i>[Hardware Accelerator]</i><br/><br/>Local GPU providing compute acceleration for PyTorch<br/>neural voice synthesis and VLM inference."]:::externalSystem
    end

    user -->|"Operates Web GUI and CLI<br/><b>[HTTP / CLI]</b>"| lektor
    lektor -->|"Sends page scans & translation prompts<br/><b>[HTTP REST / SSE]</b>"| visionServer
    lektor -->|"Reads scans, writes Markdown & WAV audio<br/><b>[OS File I/O]</b>"| filesystem
    lektor -->|"Runs PyTorch neural synthesis & monitors VRAM<br/><b>[CUDA / PyTorch API]</b>"| cuda
```

## Boundaries and responsibilities

* **User**: Interacts with the platform through the browser UI on port 7860 (or port 80 via local TCP port forwarding) or the CLI console.
* **Lektor Pro**: Core orchestration system implemented in Python 3.14 conforming to clean architecture. It coordinates conversion workflows, linguistic normalization, audio signal cleaning, and dynamic resource leasing.
* **Local multimodal AI engine**: Independent process hosting the visual-language model. It converts scanned page bitmaps to normalized Polish Markdown with preserved Go code listings and Mermaid diagrams.
* **Host file system**: Single source of truth for all persistent entities organized under `data/books/<slug>/`.
* **NVIDIA CUDA hardware**: Dedicated hardware accelerator shared sequentially by VLM and TTS models via the dynamic VRAM arbiter.
