"""lektor/adapters/gui/broadcaster.py."""

import asyncio
from typing import AsyncIterator
from ...application.ports.telemetry_ports import TelemetryBroadcasterProtocol
from ...domain.conversion_models import ConversionTaskId, ConversionTelemetry


class SseTelemetryBroadcasterAdapter(TelemetryBroadcasterProtocol):
  """Manages SSE event queue subscriptions for active tasks."""

  def __init__(self) -> None:
    self._subscribers: dict[str, list[asyncio.Queue[ConversionTelemetry]]] = {}
    self._latest_telemetry: dict[str, ConversionTelemetry] = {}
    self._loop: asyncio.AbstractEventLoop | None = None

  def broadcast(self, telemetry: ConversionTelemetry) -> None:
    """Broadcasts new event to all connected clients."""
    task_key = str(telemetry.task_id)
    self._latest_telemetry[task_key] = telemetry

    queues = self._subscribers.get(task_key, [])
    for q in queues:
      if self._loop and self._loop.is_running():
        # Implementation note: see the surrounding code for the behavior described here.
        self._loop.call_soon_threadsafe(self._safe_put, q, telemetry)
      else:
        self._safe_put(q, telemetry)

  @staticmethod
  def _safe_put(
      q: asyncio.Queue[ConversionTelemetry], item: ConversionTelemetry
  ) -> None:
    try:
      q.put_nowait(item)
    except asyncio.QueueFull:
      pass

  async def subscribe(
      self, task_id: ConversionTaskId
  ) -> AsyncIterator[ConversionTelemetry]:
    """Creates asynchronous telemetry event generator for given task ID."""
    self._loop = asyncio.get_running_loop()
    task_key = str(task_id)
    queue: asyncio.Queue[ConversionTelemetry] = asyncio.Queue(maxsize=100)

    if task_key not in self._subscribers:
      self._subscribers[task_key] = []
    self._subscribers[task_key].append(queue)

    if task_key in self._latest_telemetry:
      await queue.put(self._latest_telemetry[task_key])

    try:
      while True:
        item = await queue.get()
        yield item
        if item.state in ("COMPLETED", "CANCELLED", "FAILED"):
          break
    finally:
      if task_key in self._subscribers and queue in self._subscribers[task_key]:
        self._subscribers[task_key].remove(queue)
        if not self._subscribers[task_key]:
          del self._subscribers[task_key]
