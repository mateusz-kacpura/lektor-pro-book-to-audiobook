"""
lektor.adapters.gui.job_manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Job execution manager coordinating background task queues.
"""

import threading
from typing import Optional

from ...application.ports.telemetry_ports import JobStatusProviderProtocol
from .schemas import GenerationParams


class JobExecutionManager(JobStatusProviderProtocol):
    """Thread-safe asynchronous and batch job manager for the Web GUI."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._active_generation: Optional[str] = None
        self._is_batch_running: bool = False
        self._batch_cancel_event: threading.Event = threading.Event()
        self._batch_thread: Optional[threading.Thread] = None
        self._current_params: GenerationParams = GenerationParams()

    @property
    def cancel_event(self) -> threading.Event:
        """Returns cancellation event instance for background operation."""
        return self._batch_cancel_event

    def get_active_generation(self) -> Optional[str]:
        with self._lock:
            return self._active_generation

    def set_active_generation(self, page_id: Optional[str]) -> None:
        with self._lock:
            self._active_generation = page_id

    def is_batch_running(self) -> bool:
        with self._lock:
            if self._is_batch_running:
                # Implementation note: see the surrounding code for the behavior described here.
                if self._batch_thread is not None and not self._batch_thread.is_alive():
                    self._is_batch_running = False
                    self._batch_cancel_event.clear()
                    self._active_generation = None
            return self._is_batch_running

    def is_busy(self) -> bool:
        with self._lock:
            return self.is_batch_running() or (self._active_generation is not None)

    def start_batch(self, thread: threading.Thread, params: Optional[GenerationParams] = None) -> None:
        with self._lock:
            if params is not None:
                self._current_params = params
            self._is_batch_running = True
            self._batch_cancel_event.clear()
            self._batch_thread = thread
            thread.start()

    def stop_batch(self) -> None:
        with self._lock:
            self._batch_cancel_event.set()

    def reset_batch_state(self) -> None:
        with self._lock:
            self._active_generation = None
            self._is_batch_running = False
            self._batch_cancel_event.clear()
            self._batch_thread = None

    def is_batch_cancelled(self) -> bool:
        return self._batch_cancel_event.is_set()

    def is_stopping(self) -> bool:
        with self._lock:
            return self._batch_cancel_event.is_set() and self.is_batch_running()

    def get_current_params(self) -> GenerationParams:
        with self._lock:
            return self._current_params

    def get_current_params_dict(self) -> dict[str, object]:
        with self._lock:
            return self._current_params.model_dump()

    def set_current_params(self, params: GenerationParams) -> None:
        with self._lock:
            self._current_params = params

    def get_batch_thread(self) -> Optional[threading.Thread]:
        with self._lock:
            return self._batch_thread
