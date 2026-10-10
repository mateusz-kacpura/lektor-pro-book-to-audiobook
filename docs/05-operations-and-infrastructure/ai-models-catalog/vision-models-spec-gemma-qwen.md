# Multimodal vision models specification (Gemma 4 & Qwen)

## Overview

This specification documents the multimodal vision-language models utilized for document analysis, technical translation, code preservation, and Mermaid diagram extraction from scanned book pages.

---

## 1. Model specifications

### Google DeepMind Gemma 4 12B (Primary)
- **Model tag**: `google/gemma-4-12b`
- **Format**: GGUF quantization (`Q4_K_M`) executed via `llama-server.exe`.
- **Visual projector**: `mmproj-gemma-4-12B-it-BF16.gguf`.
- **Context window**: 8,192 tokens.
- **VRAM footprint**: ~7.5 to 8.2 GB with 99 layers offloaded to CUDA.
- **Strengths**: High comprehension of Polish grammatical nuances, structural preservation of Go source code, precise identification of flowchart node connections.

### Qwen 2.5 VL 7B (Secondary / Fallback)
- **Model tag**: `qwen2.5-vl:7b`
- **Format**: GGUF / Ollama endpoint on port 11434.
- **VRAM footprint**: ~5.5 to 6.2 GB.
- **Strengths**: Fast page transcription throughput and high optical character recognition accuracy on small typography.

---

## 2. Prompt engineering contract

Prompt definitions are enforced by `DefaultVisionPromptBuilder`:

- **System prompt**: Establishes technical translation persona, instructs literal code preservation, demands diagram transcription to ```` ```mermaid ````, and mandates exclusion of running headers or margin page numbers.
- **User prompt**: Delivers the high-resolution page image payload with strict formatting guidelines.

---

## 3. Quantization and memory guidelines

| Model variant | Quantization | Size on disk | Min VRAM required | Layers offloaded |
| :--- | :--- | :--- | :--- | :--- |
| Gemma 4 12B | `Q4_K_M` | ~7.2 GB | 10.0 GB | 99 (all layers) |
| Qwen 2.5 VL 7B | `Q4_K_M` | ~4.8 GB | 8.0 GB | 99 (all layers) |
