# Adapter telemetrii karty graficznej

## Przegląd

Adapter `NvidiaSmiGpuTelemetryAdapter` (`lektor.adapters.gui.gpu_adapter`) realizuje kontrakt `GpuTelemetryProtocol`. Odpytuje sterownik karty graficznej w czasie rzeczywistym o zajętość pamięci VRAM, całkowitą pojemność oraz procentowe obciążenie rdzeni CUDA bez konieczności wiązania ciężkich bibliotek C.

---

## 1. Mechanizm komunikacji ze sterownikiem

Adapter wywołuje narzędzie systemowe `nvidia-smi` w nieblokującym podprocesie z limitem czasu:

```bash
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits

```

```mermaid
sequenceDiagram
    autonumber
    participant App as Aplikacja / Strumień SSE
    participant Adapter as NvidiaSmiGpuTelemetryAdapter
    participant Driver as Narzędzie nvidia-smi

    App->>Adapter: get_gpu_stats()
    activate Adapter
    Adapter->>Driver: Wywołanie zapytania (timeout 2.0s)
    alt Sukces
        Driver-->>Adapter: "1250, 12288, 14"
        Adapter->>Adapter: Parsowanie liczb zmiennoprzecinkowych
        Adapter-->>App: (1250.0, 12288.0, 14.0)
    else Brak sterownika / Błąd
        Adapter-->>App: (0.0, 0.0, 0.0) [Bezpieczny fallback]
    end
    deactivate Adapter

```

---

## 2. Niezmienniki i odporność na błędy

* **Ochrona przed awarią**: Jeśli aplikacja działa w środowisku bez karty NVIDIA lub narzędzie `nvidia-smi` nie jest zainstalowane, adapter przechwytuje wyjątek i zwraca bezpieczną krotkę `(0.0, 0.0, 0.0)`.
* **Limit czasu zapytania**: Każde wywołanie sterownika ma sztywny limit czasu $2{,}0\text{ s}$, co zapobiega zawieszeniu pętli telemetrii.