# System context (level 1)

## Overview

The system context diagram shows the high-level boundary of the Lektor Pro application, the primary users, and external integrations. Lektor Pro operates locally on workstation hardware, providing end-to-end processing from raw technical book scans to synthesized speech audio.

```mermaid
C4Context
    title System Context Diagram - Lektor Pro

    Person(user, "Software Engineer / Reader", "Listens to audiobooks, studies technical text, reads code and architectural diagrams.")

    System(lektor, "Lektor Pro Platform", "Local system converting technical books (PDF/scans) to Markdown, generating audio, and providing a web-based player and Markdown studio.")

    System_Ext(visionServer, "Local Multimodal AI Engine", "Local LLM/VLM process (e.g. llama-server running Gemma 4 or Qwen2.5-VL via OpenAI-compatible API).")
    System_Ext(filesystem, "Host File System", "Local data storage: PDF files, scanned images, generated Markdown pages, and PCM WAV audio buffers.")
    System_Ext(cuda, "NVIDIA CUDA Hardware", "Local GPU providing computational acceleration for PyTorch neural voice synthesis and VLM inference.")

    Rel(user, lektor, "Uses Web GUI and CLI to import, convert, generate audio, and listen", "HTTP / CLI")
    Rel(lektor, filesystem, "Reads source scans and writes processed pages, WAV tracks, and telemetry logs", "File I/O")
    Rel(lektor, visionServer, "Sends high-resolution page scans and translation prompts", "HTTP REST / SSE")
    Rel(lektor, cuda, "Executes PyTorch neural synthesis (OmniVoice/Chatterbox) and monitors VRAM", "CUDA C++ / PyTorch API")

```

## Boundaries and responsibilities

* **User**: Interacts with the platform through the browser UI on port 7860 (or port 80 via local TCP port forwarding) or the CLI console.
* **Lektor Pro**: Core orchestration system implemented in Python 3.14 conforming to clean architecture. It coordinates conversion workflows, linguistic normalization, audio signal cleaning, and dynamic resource leasing.
* **Local multimodal AI engine**: Independent process hosting the visual-language model. It converts scanned page bitmaps to normalized Polish Markdown with preserved Go code listings and Mermaid diagrams.
* **Host file system**: Single source of truth for all persistent entities organized under `data/books/<slug>/`.
* **NVIDIA CUDA hardware**: Dedicated hardware accelerator shared sequentially by VLM and TTS models via the dynamic VRAM arbiter.
