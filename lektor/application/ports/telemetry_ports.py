"""
lektor.application.ports.telemetry_ports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Input/output ports for progress notifications, SSE telemetry, and GPU monitoring.
Strict typing without Any.
"""

from pathlib import Path
from typing import AsyncIterator, Optional, Protocol

from ...domain.audio_models import SynthesisResult
from ...domain.conversion_models import ConversionTaskId, ConversionTelemetry


class ProgressReporterProtocol(Protocol):
    """Abstract contract for synthesis/conversion progress notifications."""

    def on_page_start(self, page_path: Path, current_idx: int, total_pages: int) -> None:
        ...

    def on_page_complete(self, result: SynthesisResult) -> None:
        ...

    def on_skipped(self, page_path: Path, reason: str) -> None:
        ...

    def on_error(self, page_path: Path, error: Exception) -> None:
        ...

    def check_cancellation(self) -> bool:
        """Returns True if the task should be cancelled."""
        ...


class TelemetryBroadcasterProtocol(Protocol):
    """Abstract contract for real-time telemetry event distributor (SSE)."""

    def broadcast(self, telemetry: ConversionTelemetry) -> None:
        """Emits telemetry event to all active subscribers."""
        ...

    def subscribe(self, task_id: ConversionTaskId) -> AsyncIterator[ConversionTelemetry]:
        """Creates asynchronous telemetry event generator for the given task ID."""
        ...


class GpuTelemetryProtocol(Protocol):
    """Abstract contract for reading GPU hardware metrics."""

    def get_gpu_stats(self) -> tuple[float, float, float]:
        """Returns tuple: (used_vram_mb, total_vram_mb, utilization_pct)."""
        ...


class JobStatusProviderProtocol(Protocol):
    """Abstract contract for checking synthesis job execution status."""

    def is_batch_running(self) -> bool:
        """Returns True if batch page processing is active."""
        ...

    def is_stopping(self) -> bool:
        """Returns True if batch cancellation was requested."""
        ...

    def get_active_generation(self) -> Optional[str]:
        """Returns ID of currently generated page or None."""
        ...

    def get_current_params_dict(self) -> dict[str, object]:
        """Returns dictionary with current speech generation parameters."""
        ...
