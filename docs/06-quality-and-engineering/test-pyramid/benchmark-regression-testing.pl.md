# Testy wydajnościowe i regresja pamięciowa

## Przegląd

Pakiet testów wydajnościowych (`tests/benchmark/`) weryfikuje przestrzeganie ścisłych limitów zużycia zasobów, czasy wykonywania operacji oraz brak wycieków pamięci podczas ciągłej pracy aplikacji.

---

## 1. Zakres testów benchmarkowych

```mermaid
flowchart TD
    Suite[Pakiet testów benchmarkowych] --> Norm[test_benchmark_normalization.py]
    Suite --> Stitch[test_benchmark_audio_stitcher.py]
    Suite --> GUI[test_benchmark_gui_throughput.py]
    Suite --> GPU[test_benchmark_gpu_hardware.py]
    Suite --> UC[test_benchmark_use_cases.py]

    Norm -->|Asercja| NormLimits[Sterta <= 25 MB / Czas <= 5s / Brak wycieków]
    Stitch -->|Asercja| StitchLimits[Sterta <= 35 MB / Czas <= 2s / Brak wycieków]
    GUI -->|Asercja| GuiLimits[Śr. czas <= 300ms / 50 zapytań / Brak wycieków]
    GPU -->|Asercja| GpuLimits[Wolny VRAM >= 2000 MB / CUDA gotowe]
    UC -->|Asercja| UcLimits[Sterta <= 20 MB na stronę / Pętla syntezy OK]

```

---

## 2. Uruchamianie benchmarków i raportowanie

Testy wydajnościowe można uruchamiać za pomocą modułu `unittest` lub dedykowanego skryptu profilującego:

```powershell
# Uruchomienie jako standardowe testy jednostkowe
python -m unittest discover -s tests/benchmark

# Uruchomienie dedykowanego skryptu z pełnym raportem tabelarycznym
python scripts/run_benchmarks.py

```

### Wyniki referencyjne (RTX 3060 12 GB, Python 3.14)

```text
Nazwa testu                      | Czas       | CPU %    | Szczyt heap  | Wycieki    | Norma
--------------------------------------------------------------------------------------------
Normalizacja tekstu (Domena)     | 3.378s     | 88.4%    | 294.51 KB    | BRAK       | OK
Łączenie i czyszczenie audio     | 3.703s     | 87.4%    | 9.95 MB      | BRAK       | OK
Przepustowość Web GUI (50 req)   | 6.909s     | 86.6%    | 1.37 MB      | BRAK       | OK
Diagnostyka sprzętowa i VRAM     | 0.051s     | 0.0%     | 293.41 KB    | BRAK       | OK
--------------------------------------------------------------------------------------------
Wszystkie testy zakończone sukcesem. Brak wycieków pamięci.

```

---

## 3. Ochrona przed regresją w potoku CI

Jeśli zmiana w kodzie spowoduje narost sterty w pętli wielokrotnej przekraczający próg `max_allowed_leak_growth_bytes` (1 do 2 MB) lub szczyt alokacji przekroczy założoną normę, test zgłasza błąd i blokuje zatwierdzenie zmian w repozytorium.
