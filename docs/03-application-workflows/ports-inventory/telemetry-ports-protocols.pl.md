# Porty i protokoły telemetrii i monitorowania

## Przegląd

Dokument zawiera specyfikację kontraktów portów dla powiadomień o postępie, dystrybucji zdarzeń Server-Sent Events (SSE), odczytu parametrów karty graficznej oraz sprawdzania stanu wątków roboczych. Zdefiniowane w module `lektor.application.ports.telemetry_ports`.

---

## 1. `ProgressReporterProtocol`

Udostępnia metody zwrotne do monitorowania długotrwałych zadań wsadowych:

```python
class ProgressReporterProtocol(Protocol):
    def on_page_start(self, page_path: Path, current_idx: int, total_pages: int) -> None:
        """Wywoływane bezpośrednio przed rozpoczęciem przetwarzania danej strony."""
        ...

    def on_page_complete(self, result: SynthesisResult) -> None:
        """Wywoływane po pomyślnym ukończeniu syntezy strony."""
        ...

    def on_skipped(self, page_path: Path, reason: str) -> None:
        """Wywoływane w przypadku pominięcia strony (np. istniejący plik audio)."""
        ...

    def on_error(self, page_path: Path, error: Exception) -> None:
        """Wywoływane po wystąpieniu błędu podczas przetwarzania strony."""
        ...

    def check_cancellation(self) -> bool:
        """Odpytywane między krokami; zwraca True, jeśli zadanie zostało przerwane."""
        ...

```

---

## 2. `TelemetryBroadcasterProtocol`

Odpowiada za asynchroniczne rozgłaszanie zdarzeń do podłączonych klientów przeglądarkowych:

```python
class TelemetryBroadcasterProtocol(Protocol):
    def broadcast(self, telemetry: ConversionTelemetry) -> None:
        """Emituje zdarzenie telemetrii do wszystkich aktywnych kolejek subskrybentów."""
        ...

    def subscribe(self, task_id: ConversionTaskId) -> AsyncIterator[ConversionTelemetry]:
        """Tworzy asynchroniczny generator zdarzeń telemetrii dla zadanego identyfikatora zadania."""
        ...

```

---

## 3. `GpuTelemetryProtocol`

Oddziela odpytywanie sterownika karty graficznej od logiki biznesowej:

```python
class GpuTelemetryProtocol(Protocol):
    def get_gpu_stats(self) -> tuple[float, float, float]:
        """Zwraca krotkę: (użyty_vram_mb, całkowity_vram_mb, procent_utylizacji)."""
        ...

```

---

## 4. `JobStatusProviderProtocol`

Udostępnia bezpieczne wątkowo zapytania o stan zadań w tle:

```python
class JobStatusProviderProtocol(Protocol):
    def is_batch_running(self) -> bool:
        """Zwraca True, jeśli trwa przetwarzanie wsadowe stron w tle."""
        ...

    def is_stopping(self) -> bool:
        """Zwraca True, jeśli zgłoszono sygnał zatrzymania przetwarzania."""
        ...

    def get_active_generation(self) -> Optional[str]:
        """Zwraca identyfikator aktualnie generowanej strony lub None."""
        ...

    def get_current_params_dict(self) -> dict[str, object]:
        """Zwraca słownik z bieżącymi parametrami generowania mowy."""
        ...

```
