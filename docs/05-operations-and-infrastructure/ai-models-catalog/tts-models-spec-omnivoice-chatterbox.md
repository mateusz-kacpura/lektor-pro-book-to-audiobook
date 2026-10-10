# Text-to-speech models specification (OmniVoice & Chatterbox)

## Overview

This specification details the neural speech synthesis models supported by Lektor Pro. Operated via `UniversalTTSEngine` (`lektor.adapters.tts.universal_engine`), these models deliver zero-shot voice cloning, bilingual language switching, and natural reading cadence.

---

## 1. Supported models comparative matrix

| Parameter | k2-fsa / OmniVoice (Default) | Resemble AI / Chatterbox |
| :--- | :--- | :--- |
| **Model identifier** | `k2-fsa/OmniVoice` | `ResembleAI/chatterbox` |
| **Architecture** | Flow matching transformer + neural vocoder | Autoregressive acoustic model + diffusion |
| **VRAM footprint** | ~2.5 to 3.2 GB | ~3.0 to 3.8 GB |
| **Native sample rate** | 24,000 Hz | 24,000 Hz |
| **Language coverage** | 600+ languages (native PL & EN) | Multilingual |
| **Voice cloning** | Zero-shot from single reference WAV | Few-shot audio prompt conditioning |
| **Inference speed** | Real-time factor (RTF) ~0.12 - 0.20 on RTX 3060 | Real-time factor (RTF) ~0.25 - 0.40 |

---

## 2. Model configuration & hyperparameters

Configured via `SynthesisConfig` in `lektor.domain.audio_models`:

- **Temperature (`temperature = 0.33`)**: Controls probabilistic token variance. Lower settings prevent pitch wobbles and mumbling on technical terms.
- **Classifier-Free Guidance (`cfg_weight = 0.68`)**: Balances text adherence against acoustic naturalness. Higher weights enforce strict phoneme match.
- **Exaggeration (`exaggeration = 0.25`)**: Tunes voice expressiveness. A low setting ensures calm, documentary-style narration suited for code analysis.
- **Repetition penalty (`repetition_penalty = 1.8`)**: Suppresses acoustic loops and stuttering on punctuation boundaries.

---

## 3. Hardware deployment requirements

- **GPU Acceleration**: CUDA 12.x compatible device with at least 4 GB available VRAM.
- **Fallback**: Automatically falls back to multi-core CPU inference via float32 tensors if CUDA is unavailable.
