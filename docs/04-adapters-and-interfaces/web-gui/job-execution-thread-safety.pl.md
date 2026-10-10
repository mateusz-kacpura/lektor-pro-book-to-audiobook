# Bezpieczeństwo wątkowe wykonywania zadań

## Przegląd

Adapter `JobExecutionManager` (`lektor.adapters.gui.jobs`) zapewnia bezpieczną wątkowo orkiestrację długotrwałych zadań syntezy wsadowej oraz konwersji wykonywanych w wątkach roboczych w tle.

---

## 1. Model współbieżności

```mermaid
sequenceDiagram
    autonumber
    participant Router as Router generatora FastAPI
    participant Mgr as JobExecutionManager
    participant Thread as Wątek roboczy (Daemon)
    participant UC as BatchSynthesisUseCase

    Router->>Mgr: start_batch(use_case, command)
    activate Mgr
    Mgr->>Mgr: Zajęcie blokady RLock
    alt Zadanie już trwa
        Mgr-->>Router: Zgłoszenie błędu JobAlreadyRunningError
    else Wolne zasoby
        Mgr->>Mgr: Wyczyszczenie stop_event
        Mgr->>Thread: Uruchomienie threading.Thread(daemon=True)
        activate Thread
        Mgr-->>Router: Potwierdzenie uruchomienia
    end
    deactivate Mgr

    Thread->>UC: execute(command)
    Note over Thread,UC: Sekwencyjne przetwarzanie stron

    Router->>Mgr: request_stop()
    activate Mgr
    Mgr->>Mgr: Ustawienie stop_event
    deactivate Mgr

    UC->>Mgr: is_stopping()? -> True
    UC->>Thread: Bezpieczne wyjście z pętli stron
    deactivate Thread

```

---

## 2. Narzędzia synchronizacji

1. **Muteks wielokrotny (`threading.RLock`)**: Zabezpiecza słowniki stanu, identyfikatory aktywnie generowanych stron oraz wskaźniki wątków przed wyścigami danych podczas równoległych zapytań o stan.
2. **Sygnalizacja zatrzymania (`threading.Event`)**: Służy jako flaga kooperacyjnego przerwania pracy. Wywołanie punktu `/api/generator/stop` ustawia flagę `stop_event`, nakazując wątkowi zakończenie przetwarzania po bieżącym segmencie.
3. **Wątki typu daemon (`daemon=True`)**: Wątki robocze działają w trybie demona, co gwarantuje natychmiastowe i czyste wyłączenie procesu aplikacji bez zawieszania serwera Uvicorn.
