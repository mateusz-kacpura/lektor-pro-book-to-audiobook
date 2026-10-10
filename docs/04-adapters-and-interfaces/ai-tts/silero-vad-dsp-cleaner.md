# Audio cleaner with Silero VAD & DSP pipeline

## Overview

The `SileroAudioCleaner` adapter (`lektor.adapters.audio.cleaner`) implements the digital signal processing (DSP) pipeline required by `BR-017`. It eliminates acoustic rumble, truncates forced end-of-sentence vocoder artifacts, reduces stationary background noise, and applies cosine edge fades.

---

## 1. Digital signal processing pipeline

```mermaid
flowchart LR
    Raw[Raw Synthesized Audio] --> HPF[4th-Order Butterworth High-Pass 75 Hz]
    HPF --> VAD[Silero VAD Speech Boundary Trim]
    VAD --> NR[Spectral Gating Noise Reduction]
    NR --> Fade[Cosine Edge Fading 15ms in / 35ms out]
    Fade --> Clean[Conditioned AudioBuffer]

```

---

## 2. DSP filter stages

### Stage 1: High-pass Butterworth filter

* **Filter order**: 4th-order forward-backward zero-phase digital filter (`scipy.signal.filtfilt`).
* **Cutoff frequency**: $75\text{ Hz}$ with sampling rate $f_s = 24{,}000\text{ Hz}$.
* **Objective**: Removes sub-audible DC bias, low-frequency hum, and vocoder baseline drifting.

### Stage 2: Silero VAD speech boundary trimming

* **Acoustic model**: Deep neural voice activity detector (`silero_vad`) loaded via TorchHub.
* **Resampling**: Downsampled internally from $24\text{ kHz}$ to $16\text{ kHz}$ for inference.
* **Threshold**: Detection confidence threshold $\theta = 0.45$.
* **Fallback**: If Silero VAD fails or detects zero frames, an RMS energy thresholding fallback operates across the trailing $400\text{ ms}$ window.
* **Padding**: Preserves a $100\text{ ms}$ safety margin after the last detected speech frame.

### Stage 3: Spectral gating noise reduction

* **Tool**: `noisereduce.reduce_noise`.
* **Parameters**: Stationary noise reduction with stationary mask evaluation to suppress ambient synthetic hiss.

### Stage 4: Raised-cosine edge fading

Smooths boundaries to avoid digital speaker pops upon segment concatenation:

* **Fade-in**: $15\text{ ms}$ linear ramp.
* **Fade-out**: $35\text{ ms}$ smooth raised-cosine curve defined by:

$$w(t) = \cos^2\left(\frac{\pi t}{2 T_{\text{fade}}}\right), \quad t \in [0, T_{\text{fade}}]$$



---

## 3. Performance bounds

* Short audio buffers ($\le 0.2\text{ s}$) bypass heavy DSP filtering to prevent signal clipping on brief interjections.
* Peak heap memory consumption during cleaning is constrained to under $10\text{ MB}$ per $40\text{ seconds}$ of audio.
