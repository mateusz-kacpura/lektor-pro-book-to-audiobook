# Czyszczenie pamięci PyTorch CUDA

## Przegląd

Klasa `PyTorchModelHandle` (`lektor.adapters.resources.arbiter`) zarządza wewnątrzprocesowymi modelami neuronowymi OmniVoice oraz Chatterbox. Odpowiada za zwrócenie pamięci GPU do sterownika systemowego w momencie wywłaszczenia przez arbitra VRAM.

---

## 1. Mechanizm zwalniania pamięci

Framework PyTorch stosuje wewnętrzny alokator pamięci podręcznej (caching allocator), aby uniknąć częstych wywołań systemowych CUDA. Samo usunięcie referencji do obiektów w Pythonie nie zwraca pamięci do sterownika bez jawnego wywołania czyszczenia:

```mermaid
sequenceDiagram
    autonumber
    participant Arbiter as DynamicVramModelArbiter
    participant Handle as PyTorchModelHandle
    participant Engine as TTSEngineProtocol
    participant GC as Odśmiecacz pamięci (GC)
    participant CUDA as Alokator PyTorch CUDA

    Arbiter->>Handle: unload()
    activate Handle
    Handle->>Engine: unload_model()
    activate Engine
    Engine-->>Handle: Wyzerowanie instancji modeli
    deactivate Engine
    
    Handle->>GC: gc.collect()
    Note over GC: Usuwa cykliczne referencje w Pythonie
    
    Handle->>CUDA: torch.cuda.empty_cache()
    Note over CUDA: Zwraca bloki pamięci do sterownika
    
    Handle->>CUDA: torch.cuda.ipc_collect()
    Note over CUDA: Czyści uchwyty pamięci międzyprocesowej
    
    Handle-->>Arbiter: Pamięć VRAM całkowicie zwolniona
    deactivate Handle

```

---

## 2. Implementacja w kodzie

```python
class PyTorchModelHandle(AIModelHandleProtocol):
    def unload(self) -> None:
        with self._lock:
            print(f"[PyTorchHandle/{self._slot_id}] Zwalnianie modelu {self._resource_id}...")
            self._engine.unload_model()
            
            # Trzyetapowe czyszczenie alokacji
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
            print(f"[PyTorchHandle/{self._slot_id}] Pamięć podręczna CUDA wyczyszczona.")

```

---

## 3. Weryfikacja działania

Skuteczność czyszczenia pamięci jest potwierdzona testami benchmarkowymi (`test_benchmark_gpu_hardware`):

* Przed wyczyszczeniem: Zajętość VRAM $\approx 3{,}2\text{ GB}$.
* Po wyczyszczeniu: Zajętość VRAM spada do poziomu bazowego sterownika ($\le 950\text{ MB}$), co zapewnia pełną przestrzeń dla modelu wizyjnego.
