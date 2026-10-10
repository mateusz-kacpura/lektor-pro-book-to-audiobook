# Protokół profilowania wycieków pamięci

## Przegląd

Narzędzie `ResourceProfiler` (`tests.benchmark.profiler`) realizuje zautomatyzowane profilowanie wycieków pamięci. Łączy migawki sterty modułu `tracemalloc` z jawnym wywoływaniem odśmiecacza pamięci w celu wykrycia nieodzyskiwalnych referencji.

---

## 1. Przebieg procedury profilowania

```mermaid
sequenceDiagram
    autonumber
    participant Runner as Zestaw benchmarków
    participant Profiler as ResourceProfiler
    participant Target as Badana funkcja
    participant GC as Odśmiecacz pamięci (GC)
    participant Trace as Moduł tracemalloc

    Runner->>Profiler: run(badana_funkcja, iteracje=30, rozgrzewka=3)
    activate Profiler
    loop Faza rozgrzewki
        Profiler->>Target: wykonanie()
    end
    Profiler->>GC: gc.collect()
    Profiler->>Trace: start() i wyczyszczenie śladów
    Profiler->>Trace: pobranie migawki początkowej

    loop Faza pomiarowa
        Profiler->>Target: wykonanie()
    end

    Profiler->>GC: gc.collect() [izolacja wycieków]
    Profiler->>Trace: pobranie migawki końcowej
    Profiler->>Trace: porównanie migawek (diff linii)

    Profiler->>Profiler: Obliczenie przyrostu sterty
    alt Przyrost > dopuszczalny próg wycieku
        Profiler-->>Runner: BenchmarkResult(leak_detected=True)
    else Czysto
        Profiler-->>Runner: BenchmarkResult(leak_detected=False)
    end
    deactivate Profiler

```

---

## 2. Kryteria wykrywania wycieków pamięci

Zadanie benchmarkowe zostaje oznaczone flagą `leak_detected = True` wtedy i tylko wtedy, gdy:

$$\sum_{\text{stat} \in \text{diff}} \max(0, \text{stat.size\_diff}) > \text{dopuszczalny\_prog\_wycieku}$$

* **Eliminacja fazy rozgrzewki**: Zapobiega fałszywym alarmom wywołanym przez jednorazowy import modułów i buforowanie struktur.
* **Wymuszone odśmiecanie pamięci**: Wywołanie `gc.collect()` przed drugą migawką gwarantuje, że obiekty cykliczne podlegające normalnemu usunięciu nie są kwalifikowane jako wyciek.
* **Śledzenie linii kodu**: Raport wynikowy rejestruje trzy linie kodu o najwyższym przyroście alokacji, ułatwiając szybką lokalizację problemu.