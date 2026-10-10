# Environment configuration (.env) runbook

## Overview

Lektor Pro uses environment variables loaded from `.env` via `load_env_file()` in `lektor.infrastructure.config` as the Single Source of Truth (SSOT). This document specifies all available configuration keys, valid options, defaults, and their architectural impact.

---

## 1. Environment variables specification

| Variable key | Default value | Valid options | Description & architectural impact |
| :--- | :--- | :--- | :--- |
| `LEKTOR_DATA_DIR` | `data` | Directory path | Root data storage directory. Dictates filesystem resolution in `DataPaths.from_data_dir()`. |
| `LEKTOR_ACTIVE_BOOK` | `cloud_native_go` | Existing book slug | Active book workspace slug within `data/books/<slug>/`. Fallback if `.active` marker is absent. |
| `LEKTOR_DEVICE` | `auto` | `auto`, `cuda`, `cpu` | Computational acceleration device. `auto` queries `torch.cuda.is_available()`. |
| `LEKTOR_GUI_HOST` | `127.0.0.1` | IP address / hostname | Binding interface for FastAPI / Uvicorn server. |
| `LEKTOR_GUI_PORT` | `7860` | TCP port (e.g. `7860`) | Web GUI listening port. |
| `LEKTOR_AUTO_OPEN_BROWSER`| `true` | `true`, `false` | Automatically opens browser window to GUI URL on startup (`run_gui.py`). |
| `LEKTOR_TTS_ENGINE` | `omnivoice` | `omnivoice`, `chatterbox`, `mock` | Default neural speech engine backend selected by `TTSEngineFactory`. |
| `LEKTOR_OMNIVOICE_MODEL` | `k2-fsa/OmniVoice` | Hugging Face ID / path | Neural weights identifier for OmniVoice multilingual flow-matching model. |
| `LEKTOR_CHATTERBOX_MODEL` | `ResembleAI/chatterbox`| Hugging Face ID / path | Model identifier for Resemble AI Chatterbox model. |
| `LEKTOR_VISION_MODEL` | `google/gemma-4-12b` | Model tag | Multimodal vision model tag passed to local or remote OpenAI-compatible endpoint. |
| `LEKTOR_VISION_API_URL` | `http://127.0.0.1:1234/v1` | URL | Target endpoint URL for OpenAI Chat Completions requests. |
| `LEKTOR_LLAMA_SERVER_BINARY`| `.../llama-server.exe` | Executable path | Absolute path to `llama-server.exe` managed by `ProcessModelHandle`. |
| `LEKTOR_LLAMA_MODEL_PATH` | `.../gemma-4-12B-it-Q4_K_M.gguf` | File path | GGUF model weights loaded by vision subprocess. |
| `LEKTOR_LLAMA_MMPROJ_PATH`| `.../mmproj-BF16.gguf` | File path | Multimodal visual projector weights for visual token embedding. |
| `LEKTOR_LLAMA_SERVER_PORT`| `1234` | TCP port | Port dedicated to `llama-server.exe` instance. |

---

## 2. Configuration loading rules

1. **Precedence hierarchy**:
   $$\text{Process Environment (OS)} > \text{.env File} > \text{InfrastructureSettings Defaults}$$
2. **Zero-dependency parser**: The custom `load_env_file()` function strips whitespace and comments without external dependencies like `python-dotenv`. Existing process variables are never overwritten.
3. **DataPaths immutability**: Once created, `DataPaths` is an immutable frozen dataclass. Reconfiguration requires an explicit call to `ApplicationContainer.reset_book_context()`.