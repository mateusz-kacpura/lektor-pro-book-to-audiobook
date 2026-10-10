# ADR-002: Dynamic VRAM arbiter and hardware resource preemption

## Context
Deploying consumer GPU hardware (such as the NVIDIA RTX 3060 with 12 GB VRAM) prevents concurrently hosting a large multimodal vision language model (Gemma 4 12B in Q4_K_M quantization requiring ~7.5 GB VRAM) alongside neural text-to-speech models (OmniVoice / Chatterbox requiring ~2.5–3.5 GB VRAM plus PyTorch runtime overhead). Loading both models concurrently causes out-of-memory crashes (`CUDA out of memory`).

## Decision
We implement a mutual-exclusion hardware resource scheduler: `DynamicVramModelArbiter` operating in the adapter layer (`lektor.adapters.resources.arbiter`).
- Models are categorized into distinct exclusive slots: `SLOT_VISION` (`vision_ocr`) and `SLOT_AUDIO_TTS` (`audio_tts`).
- When a task requires `SLOT_VISION`, the arbiter checks if `SLOT_AUDIO_TTS` holds GPU memory. If active, it evicts the PyTorch model, runs garbage collection, and calls `torch.cuda.empty_cache()` and `torch.cuda.ipc_collect()`.
- When a task requires `SLOT_AUDIO_TTS`, the arbiter preempts the external vision server (`llama-server.exe`) by terminating its OS process and waiting for full VRAM reclamation before loading PyTorch weights.
- Application use cases acquire slots through context managers or explicit acquisition before execution.

## Consequences
- **Positive:**
  - Eliminates CUDA OOM crashes completely on 12 GB consumer graphics cards.
  - Allows full model parameter utilization and larger context windows for each pipeline stage.
- **Negative:**
  - Inter-stage transitions incur an eviction and reload latency of approximately 1.5–3.5 seconds.ng.
