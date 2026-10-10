# Job execution & thread safety

## Overview

The `JobExecutionManager` adapter (`lektor.adapters.gui.jobs`) provides thread-safe orchestration for long-running batch synthesis tasks and conversion jobs executed within background threads.

---

## 1. Concurrency model

```mermaid
sequenceDiagram
    autonumber
    participant Router as FastAPI Generator Router
    participant Mgr as JobExecutionManager
    participant Thread as Background Daemon Thread
    participant UC as BatchSynthesisUseCase

    Router->>Mgr: start_batch(use_case, command)
    activate Mgr
    Mgr->>Mgr: acquire RLock
    alt Job already running
        Mgr-->>Router: Raise JobAlreadyRunningError
    else Free
        Mgr->>Mgr: clear stop_event
        Mgr->>Thread: spawn threading.Thread(target=run, daemon=True)
        activate Thread
        Mgr-->>Router: Return Success
    end
    deactivate Mgr

    Thread->>UC: execute(command)
    Note over Thread,UC: Executes pages sequentially

    Router->>Mgr: request_stop()
    activate Mgr
    Mgr->>Mgr: set stop_event
    deactivate Mgr

    UC->>Mgr: is_stopping()? -> True
    UC->>Thread: Abort page loop cleanly
    deactivate Thread

```

---

## 2. Synchronization primitives

1. **Reentrant mutex (`threading.RLock`)**: Protects shared state dictionaries, active generation identifiers, and worker pointers against race conditions during status queries.
2. **Cancellation signaling (`threading.Event`)**: Acts as a cooperative abort flag. When `/api/generator/stop` is invoked, `stop_event.set()` signals workers to halt processing after finishing the active utterance.
3. **Daemon threads (`daemon=True`)**: Background workers run in daemon mode, ensuring they do not prevent application shutdown when Uvicorn terminates.
