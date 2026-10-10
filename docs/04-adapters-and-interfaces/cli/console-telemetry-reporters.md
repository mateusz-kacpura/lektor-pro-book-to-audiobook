# Console telemetry reporters

## Overview

The `ConsoleProgressReporter` adapter (`lektor.adapters.cli.reporters`) implements the `ProgressReporterProtocol` contract. It provides interactive terminal feedback, progress bars, throughput metrics, and cooperative cancellation listeners during long-running tasks.

---

## 1. Visual output and event hooks

The reporter handles execution hooks emitted by batch use cases:

- `on_page_start(page_path, current_idx, total_pages)`: Renders page indicators and updates progress percentage.
- `on_page_complete(result)`: Prints duration, synthesis throughput (real-time factor), and storage paths.
- `on_skipped(page_path, reason)`: Emits non-blocking skip notices (e.g. existing audio).
- `on_error(page_path, error)`: Prints error traces while ensuring the batch loop continues (`BR-013`).

```text
[Batch Generator] [42/120] Generowanie: page_042.md
 -> Segmenty: 18 (Częściowo w cache: 12, Nowe: 6)
 -> Ukończono stronę: page_042.wav (Czas: 3.71s, RTF: 0.14)

```

---

## 2. Cancellation handling

The reporter catches terminal interruption signals (`SIGINT` / Ctrl+C) and sets internal cancellation flags:

```python
def check_cancellation(self) -> bool:
    return self._cancel_signaled

```

When signaled, use cases complete active segment saves, flush open files, and terminate cleanly without leaving corrupted audio headers.
