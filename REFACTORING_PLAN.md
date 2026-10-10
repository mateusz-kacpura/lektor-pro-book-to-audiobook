
### Faza 1: Eliminacja ukrytych zależności do konfiguracji w adapterach (Czysty DIP)

Adaptery persystencji i audio posiadają obecnie niejawne fallbacki do modułu konfiguracji (`from ...infrastructure.config import settings`), co narusza zasadę Dependency Inversion Principle i utrudnia testowanie jednostkowe.

1. **Wymuszenie Constructor Injection w repozytoriach i adapterach cache:**
* W `lektor/adapters/storage/arena_repository.py`, `notes_repository.py`, `studio_repository.py` oraz `lektor/adapters/tts/cache.py` usuń domyślną wartość `None` oraz leniwy import `settings`.


* Zmień sygnaturę konstruktorów na bezwzględnie wymagające obiektów `Path`:
```python
# Przed:
def __init__(self, stats_file: Path | str | None = None) -> None: ...
# Po:
def __init__(self, stats_file: Path) -> None:
    self.stats_file = stats_file.resolve()
    self.stats_file.parent.mkdir(parents=True, exist_ok=True)

```


* W `lektor/adapters/storage/book_repository.py` wyeliminuj sięganie do `settings.data_paths.active_book_slug` w metodzie `get_active_book()`. Przekaż domyślny slug w `__init__` (np. `default_active_slug: str = "cloud_native_go"`).




2. **Refaktoryzacja `lektor/adapters/gui/paths.py`:**
* Usuń leniwe wywołanie `settings` wewnątrz funkcji `create_gui_paths()`. Funkcja powinna przyjmować jawnie instancję `DataPaths` oraz `base_dir` jako parametry wymagane.


* Zlikwiduj eksporty zmiennych globalnych na poziomie modułu (`BASE_DIR`, `DATA_DIR`, `BOOKS_DIR` itp.), delegując zarządzanie ścieżkami wyłącznie do obiektu `ApplicationContainer`.





---

### Faza 2: Unifikacja Composition Root (Współdzielenie kontenera IoC)

CLI tworzy obecnie własne instancje adapterów i use cases niezależnie od Web GUI, co powoduje redundancję kodu fabrykującego oraz rozproszenie punktów inicjalizacji.

```
       [ punkt startowy: CLI ]       [ punkt startowy: FastAPI ]
                  \                          /
                   v                        v
          +--------------------------------------+
          |  ApplicationContainer (Infrastruktura)|
          +--------------------------------------+
              |                 |              |
              v                 v              v
         [ Repozytoria ]   [ Use Cases ]   [ Silniki TTS ]

```

1. **Przeniesienie `ApplicationContainer` do warstwy infrastruktury:**
* Przenieś `ApplicationContainer` z `lektor/adapters/gui/container.py` do nowo wydzielonego katalogu: `lektor/infrastructure/container.py`.


* Kontener staje się centralnym punktem tworzenia grafu zależności (Composition Root) dla całej aplikacji, a nie tylko dla adaptera Web GUI.


2. **Podpięcie `lektor/adapters/cli/main.py` pod kontener:**
* Zastąp ręczne instancjonowanie (`FileSystemBookRepository()`, `FileSystemPageRepository()`, `NumpyAudioStitcher()`) pobraniem gotowych use cases z kontenera:


```python
container = ApplicationContainer()
if args.command == "preview":
    uc = container.create_preview_page_use_case()
    ...

```


* Zlikwiduj rozproszone singletony modułowe (`default_telemetry_broadcaster`, `default_gpu_telemetry`, `default_audio_cleaner`), przenosząc zarządzanie ich cyklem życia do kontenera.





---

### Faza 3: Izolacja portów aplikacji od zależności zewnętrznych (`numpy`)

W pliku `lektor/application/ports/audio_ports.py` interfejsy `TTSEngineProtocol`, `AudioStitcherProtocol`, `AudioCleanerProtocol` oraz `AudioCacheProtocol` bezpośrednio referencjonują typ `np.ndarray` z biblioteki NumPy.

1. **Wprowadzenie typu domenowego dla bufora próbek mowy:**
* W `lektor/domain/audio_models.py` zdefiniuj domenową reprezentację bufora audio, np. jako `NewType` lub lekki obiekt wartości bazujący na buforze pamięci:
```python
from typing import NewType, Sequence
import numpy as np

# Opcja A (praktyczna): Silnie typowany alias domenowy
AudioBuffer = NewType("AudioBuffer", np.ndarray)

# Opcja B (purystyczna): Value Object opakowujący bufor
@dataclass(frozen=True)
class AudioChunk:
    samples: Sequence[float] | memoryview
    sample_rate: int = 24000

```




2. **Aktualizacja kontraktów w `application/ports/audio_ports.py`:**
* Zastąp surowe `np.ndarray` typem domenowym `AudioBuffer` w deklaracjach protokołów.


* Bezpośrednie operacje tablicowe (`np.concatenate`, `signal.filtfilt`, `librosa.feature.rms`) pozostają hermetycznie zamknięte wyłącznie w adapterach: `NumpyAudioStitcher` i `SileroAudioCleaner`.





---

### Faza 4: Strukturyzacja piramidy testów i konfiguracji CI

Obecna konfiguracja `.github/workflows/ci.yml` wykonuje płaskie polecenie `python -m unittest discover -s tests`, zacierając granice między testami jednostkowymi a integracyjnymi.

1. **Reorganizacja fizycznej struktury katalogu `tests/`:**
* `tests/unit/domain/` — weryfikacja logiki czyszczenia tekstu, leksemów Go, normalizacji liczb i reguł fonetycznych (brak I/O, wykonanie w milisekundach).
* `tests/unit/application/` — testy orkiestracji przypadków użycia (`SynthesizePageUseCase`, `ConvertPdfBookUseCase`) z wykorzystaniem `MockTTSEngine` i atrap repozytoriów w pamięci (in-memory test doubles).


* `tests/integration/` — testy adapterów ze stanem dyskowym (`FileSystemBookRepository`, `PyMuPdfSplitterAdapter`, `NumpyAudioStitcher`).


* `tests/e2e/` — testy pełnych scenariuszy HTTP (`FastAPI TestClient` / `httpx.AsyncClient`) oraz poleceń CLI.




2. **Dostosowanie potoku w `.github/workflows/ci.yml`:**
* Rozdziel zadanie uruchamiania testów na jawne etapy piramidy testowej:


```yaml
- name: Run Unit Tests (Domain & Use Cases)
  run: python -m unittest discover -s tests/unit

- name: Run Integration Tests (Adapters & Storage)
  run: python -m unittest discover -s tests/integration

- name: Run End-to-End Tests (CLI & API Routes)
  run: python -m unittest discover -s tests/e2e

```





---

### Harmonogram wdrożenia zmian

| Krok | Zakres plików | Ryzyko regresji | Weryfikacja |
| --- | --- | --- | --- |
| **1. Refaktoryzacja repozytoriów** | `lektor/adapters/storage/*`, `tts/cache.py`<br> | Niskie | `mypy --config-file references/mypy.ini lektor`<br> |
| **2. Przeniesienie kontenera IoC** | `lektor/infrastructure/container.py`, `gui/dependencies.py`<br> | Średnie | Testy endpointów FastAPI i podnoszenia aplikacji

 |
| **3. Przepięcie CLI na kontener** | `lektor/adapters/cli/main.py`<br> | Niskie | Weryfikacja komend `preview`, `books`, `single` z flagą `--mock`<br> |
| **4. Typ domenowy dla audio** | `lektor/domain/audio_models.py`, `ports/audio_ports.py`<br> | Średnie | Sprawdzenie zgodności sygnatur w adapterach audio

 |
| **5. Rozdzielenie testów** | Katalog `tests/`, `.github/workflows/ci.yml`<br> | Niskie | Uruchomienie lokalnego potoku unittest

### Etap 1: Oczyszczenie kierunku zależności (Composition Root & IoC)

**Cel:** Całkowite wyeliminowanie importów z warstwy `infrastructure/` wewnątrz warstwy `adapters/` (`adapters/gui/dependencies.py`, `adapters/gui/container.py`, `adapters/cli/main.py`), aby adaptery nie zależały od warstwy zewnętrznej.

1. **Wstrzykiwanie kontenera do FastAPI przez `app.state`:**
* Zmiana funkcji inicjalizującej aplikację w `lektor/adapters/gui/app.py` na fabrykę `create_app(container: ApplicationContainerProtocol | object) -> FastAPI`:
```python
def create_app(container: object) -> FastAPI:
    app = FastAPI(title="Lektor Pro")
    app.state.container = container
    # rejestracja middleware i routerów
    return app

```


* W `lektor/adapters/gui/dependencies.py` pobieranie kontenera bezpośrednio z żądania HTTP:
```python
from fastapi import Request

def get_container(request: Request) -> ApplicationContainerProtocol:
    return request.app.state.container

```


* Usunięcie modułu `lektor/adapters/gui/container.py`, który re-eksportował instancję z `infrastructure.container`.




2. **Refaktoryzacja punktu wejścia CLI (`adapters/cli/main.py`):**
* Usunięcie bezpośredniego importu `from ...infrastructure.config import settings` oraz `from ...infrastructure.container import ApplicationContainer` z wnętrza adaptera CLI.


* Przeniesienie tworzenia instancji `ApplicationContainer` oraz odczytu `settings` do nadrzędnego pliku uruchomieniowego (np. `lektor/__main__.py` lub dedykowanego runnera infrastruktury) i przekazanie zainicjalizowanego kontenera do `main(container, args_list)`.





---

### Etap 2: Separacja odpowiedzialności stanu procesów w tle (SRP)

**Cel:** Usunięcie obsługi pliku `.generator_state.json` z `PageRepositoryProtocol` i uniezależnienie repozytorium stron Markdown od ulotnego stanu zadań wsadowych.

1. **Zdefiniowanie nowego portu w `application/ports/telemetry_ports.py`:**
```python
from typing import Optional, Protocol

class JobStateStorageProtocol(Protocol):
    """Kontrakt trwałego lub pamięciowego zapisu stanu aktywnego zadania wsadowego."""
    def read_active_state(self) -> Optional[dict[str, object]]: ...
    def write_active_state(self, state: dict[str, object]) -> None: ...
    def clear_active_state(self) -> None: ...

```


2. **Implementacja adaptera w `adapters/gui/job_manager.py` lub `adapters/storage/`:**
* Przeniesienie operacji I/O na `.generator_state.json` bezpośrednio do `JobExecutionManager` (lub utworzenie `FileSystemJobStateRepository(audio_dir: Path)`).


* Klasa `GuiBatchProgressReporter` w `adapters/gui/routers/generator.py` deleguje zapis stanu do `job_mgr.write_active_state(...)` zamiast manualnego zapisu pliku przez dysk.




3. **Aktualizacja `GetBookStatusUseCase` (`application/use_cases/get_book_status.py`):**
* Wstrzyknięcie `JobStateStorageProtocol` (lub pobieranie stanu wyłącznie przez `JobStatusProviderProtocol`).


* Eliminacja wywołań `self._page_repo.page_exists(state_file)` i `self._page_repo.read_markdown(state_file)` dla plików nienależących do domeny stron Markdown.





---

### Etap 3: Uszczelnienie typowania statycznego i eliminacja typów `object`

**Cel:** Zastąpienie generycznych adnotacji `object` precyzyjnymi protokołami lub uniami typów zgodnie z wymogiem *zero Any* i regułami `mypy`.

1. **Doprecyzowanie typów modeli w `adapters/audio/cleaner.py`:**
* Zastąpienie `_vad_model: Optional[object]` oraz `_vad_utils: Optional[Sequence[object]]` dedykowanym protokołem `SileroVadCallableProtocol` lub typem `torch.nn.Module`:
```python
class VadCallable(Protocol):
    def __call__(
        self, audio: torch.Tensor, model: object, sampling_rate: int, **kwargs: float | int
    ) -> list[dict[str, int]]: ...

```




2. **Doprecyzowanie backendów TTS w `adapters/tts/backends/`:**
* Zamiana `_model: Optional[object]` w `OmniVoiceBackend` i `ChatterboxBackend` na interfejsy protokołów udostępniające metody `.generate(...)` i atrybut `.sr` / `.sampling_rate`.




3. **Usunięcie rzutowań `cast(dict[str, object], ...)` w repozytoriach:**
* W `arena_repository.py`, `interview_repository.py` oraz `studio_repository.py` zastąpienie niebezpiecznych rzutowań `cast` walidacją typu w czasie wykonania (`isinstance(item, dict)`).





---

### Etap 4: Aktualizacja testów i automatyzacja weryfikacji

**Cel:** Potwierdzenie integralności po refaktoryzacji zgodnie z hierarchią piramidy testów i konfiguracją potoku CI/CD.

1. **Testy jednostkowe (`tests/unit/`):**
* Zweryfikowanie `GetBookStatusUseCase` przy użyciu nowo zdefiniowanego mocka `JobStateStorageProtocol`.


* Weryfikacja pełnej izolacji warstwy `domain` i `application` od zewnętrznych modułów I/O.




2. **Testy integracyjne (`tests/integration/`):**
* Sprawdzenie fabryki `create_app` i weryfikacja czy routery FastAPI poprawnie pobierają zależności z `request.app.state.container` bez odwołań do zmiennych globalnych.




3. **Uruchomienie potoku kontrolnego:**
```bash
# 1. Sprawdzenie lintera i nieużywanych importów
python -m ruff check --select F,ARG lektor tests

# 2. Rygorystyczna kontrola typów bez Any
python -m mypy --config-file references/mypy.ini lektor tests

# 3. Zestaw testów jednostkowych, integracyjnych i E2E
python -m unittest discover -s tests/unit
python -m unittest discover -s tests/integration
python -m unittest discover -s tests/e2e
