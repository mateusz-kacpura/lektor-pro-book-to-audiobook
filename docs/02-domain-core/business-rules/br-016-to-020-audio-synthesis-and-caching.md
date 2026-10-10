# Business rules: audio synthesis & caching (BR-016 to BR-020)

## Overview

These business rules define constraints for speech generation, audio segment stitching, digital signal processing (DSP), and content-addressable caching.

---

### BR-016: Deterministic content-addressable audio caching

- **Statement**: Speech synthesis segments must be cached using a deterministic SHA-256 hash calculated over synthesis parameters.
- **Invariant**: The cache key hash is computed as:
  $$\text{hash} = \text{SHA256}(\text{normalized\_text} \mathbin{\Vert} \text{lang} \mathbin{\Vert} \text{voice} \mathbin{\Vert} \text{temp} \mathbin{\Vert} \text{cfg})$$
- **Storage Layout**: Cached arrays are stored on disk in two-character prefix buckets: `cache_dir/<hash[:2]>/<hash>.npy`.
- **Enforcement**: Handled by `AudioSegmentCache` in `lektor.adapters.tts.cache`. If a cache hit occurs, audio is loaded in $0\text{ ms}$ without GPU invocation.

---

### BR-017: Four-stage audio signal cleaning (DSP pipeline)

- **Statement**: Every synthesized speech buffer exceeding 0.2 seconds must pass through a strict four-stage signal conditioning pipeline.
- **Invariant**: Processing must follow this sequence:
  1. **High-Pass Filter**: 4th-order Butterworth filter at $75\text{ Hz}$ to eliminate vocoder rumble.
  2. **Boundary Trimming**: Silero VAD speech detection at $16\text{ kHz}$ to slice forced EOS artifacts (falling back to RMS energy thresholding).
  3. **Spectral Noise Reduction**: Stationary background noise attenuation via `noisereduce`.
  4. **Smooth Edge Fading**: $15\text{ ms}$ linear fade-in and $35\text{ ms}$ raised-cosine fade-out ($\cos^2$).
- **Enforcement**: Handled by `SileroAudioCleaner` in `lektor.adapters.audio.cleaner`.

---

### BR-018: Peak volume normalization and clipping prevention

- **Statement**: Concatenated audio tracks must be normalized to prevent digital clipping before saving to disk.
- **Invariant**:
  $$\text{normalized\_audio} = \left( \frac{\text{audio}}{\max(\vert{}\text{audio}\vert{})} \right) \times 0.95$$
  The peak amplitude must not exceed $0.95$ ($-0.45\text{ dBFS}$).
- **Enforcement**: Executed by `NumpyAudioStitcher.normalize_volume`.

---

### BR-019: Hardware mutual exclusion on single GPU (VRAM Arbiter)

- **Statement**: The VLM model (`SLOT_VISION`) and TTS engine (`SLOT_AUDIO_TTS`) must never reside concurrently in GPU memory on 12 GB VRAM hardware.
- **Invariant**: Acquiring `SLOT_AUDIO_TTS` triggers immediate preemption: terminating `llama-server.exe`, waiting for process release, and verifying free memory. Acquiring `SLOT_VISION` unloads PyTorch weights, runs garbage collection, and flushes the CUDA cache.
- **Enforcement**: Governed by `DynamicVramModelArbiter.acquire` in `lektor.adapters.resources.arbiter`.

---

### BR-020: Standard audio export format

- **Statement**: All finalized book pages and studio recordings must be written as linear PCM 16-bit WAV files at a $24{,}000\text{ Hz}$ sampling rate.
- **Invariant**: Format specification requires `sample_rate = 24000`, `subtype = PCM_16`, and single-channel mono layout.
- **Enforcement**: Verified by `AudioSpec` and enforced in `NumpyAudioStitcher.save_audio`.
