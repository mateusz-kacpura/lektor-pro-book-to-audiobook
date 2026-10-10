# Konsolowe reportery telemetrii

## Przegląd

Adapter `ConsoleProgressReporter` (`lektor.adapters.cli.reporters`) implementuje kontrakt `ProgressReporterProtocol`. Dostarcza wizualne komunikaty w terminalu, paski postępu, metryki przepustowości oraz obsługę sygnałów przerwania podczas długotrwałych zadań wsadowych.

---

## 1. Format komunikatów i obsługa zdarzeń

Reporter reaguje na wywołania zwrotne z przypadków użycia:

- `on_page_start(page_path, current_idx, total_pages)`: Wyświetla numer bieżącej strony i aktualny procent wykonania zadania.
- `on_page_complete(result)`: Wypisuje czas trwania, współczynnik czasu rzeczywistego (RTF) oraz ścieżkę do pliku wyjściowego.
- `on_skipped(page_path, reason)`: Informuje o pominięciu strony (np. istniejące nagranie audio).
- `on_error(page_path, error)`: Rejestruje błąd w konsoli z zachowaniem ciągłości przetwarzania pozostałych stron (`BR-013`).

```text
[Batch Generator] [42/120] Generowanie: page_042.md
 -> Segmenty: 18 (Częściowo w cache: 12, Nowe: 6)
 -> Ukończono stronę: page_042.wav (Czas: 3.71s, RTF: 0.14)

```

---

## 2. Obsługa przerwania zadania

Reporter przechwytuje sygnały przerwania z klawiatury (`SIGINT` / Ctrl+C) i ustawia flagę kooperacyjnego zatrzymania:

```python
def check_cancellation(self) -> bool:
    return self._cancel_signaled

```

Po odebraniu sygnału przypadek użycia dokańcza zapis bieżącego segmentu, zamyka pliki i bezpiecznie kończy działanie bez uszkadzania nagłówków WAV.
