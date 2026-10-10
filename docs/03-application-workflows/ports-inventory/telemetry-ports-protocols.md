# Telemetry ports & protocols

## Overview

This specification details port contracts for real-time progress notifications, Server-Sent Events (SSE) broadcasting, hardware telemetry readings, and background worker status queries. Defined in `lektor.application.ports.telemetry_ports`.

---

## 1. `ProgressReporterProtocol`

Provides hooks for monitoring long-running batch conversion and synthesis operations:

```python
class ProgressReporterProtocol(Protocol):
    def on_page_start(self, page_path: Path, current_idx: int, total_pages: int) -> None:
        """Invoked immediately before processing a page begins."""
        ...

    def on_page_complete(self, result: SynthesisResult) -> None:
        """Invoked when a page finishes synthesis successfully."""
        ...

    def on_skipped(self, page_path: Path, reason: str) -> None:
        """Invoked when a page is bypassed (e.g. existing cache)."""
        ...

    def on_error(self, page_path: Path, error: Exception) -> None:
        """Invoked when an exception occurs on an individual page."""
        ...

    def check_cancellation(self) -> bool:
        """Polled between iterations; returns True if the task was aborted."""
        ...

```

---

## 2. `TelemetryBroadcasterProtocol`

Governs asynchronous event streaming to connected web client subscribers:

```python
class TelemetryBroadcasterProtocol(Protocol):
    def broadcast(self, telemetry: ConversionTelemetry) -> None:
        """Emits a telemetry event snapshot to all connected client queues."""
        ...

    def subscribe(self, task_id: ConversionTaskId) -> AsyncIterator[ConversionTelemetry]:
        """Creates an async event iterator yielding telemetry items for a task."""
        ...

```

---

## 3. `GpuTelemetryProtocol`

Decouples driver querying from application workflows:

```python
class GpuTelemetryProtocol(Protocol):
    def get_gpu_stats(self) -> tuple[float, float, float]:
        """Returns tuple of (used_vram_mb, total_vram_mb, utilization_pct)."""
        ...

```

---

## 4. `JobStatusProviderProtocol`

Provides thread-safe queries into active worker threads:

```python
class JobStatusProviderProtocol(Protocol):
    def is_batch_running(self) -> bool:
        """Returns True if a batch synthesis background thread is active."""
        ...

    def is_stopping(self) -> bool:
        """Returns True if cancellation has been signaled to workers."""
        ...

    def get_active_generation(self) -> Optional[str]:
        """Returns identifier of page currently being synthesized on GPU, or None."""
        ...

    def get_current_params_dict(self) -> dict[str, object]:
        """Returns dictionary of active speech generation parameters."""
        ...

```