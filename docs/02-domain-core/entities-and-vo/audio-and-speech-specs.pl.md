# Parametry audio i mowy

## Przegląd

Dokument zawiera specyfikację struktur domenowych, niezmiennych obiektów wartości (ang. *value objects*) oraz modeli konfiguracyjnych odpowiedzialnych za reprezentację sygnału dźwiękowego, segmentację wypowiedzi i metryki przetwarzania audio.

---

## 1. Typy domenowe i literały

Zdefiniowane w module `lektor.domain.audio_models`, typy te określają tryb językowy, sposób odczytu kodu oraz formaty wyjściowe:

```python
LanguageMode = Literal["bilingual", "pl", "en"]
CodeMode = Literal["spoken", "literal", "skip"]
AudioFormat = Literal["wav", "mp3", "flac"]

```

* **`LanguageMode`**: Steruje normalizacją tekstu. W trybie `bilingual` treść czytana jest po polsku, natomiast terminy techniczne i kod z natywnym akcentem angielskim.
* **`CodeMode`**: Określa sposób czytania kodu: `spoken` tłumaczy idiomy Go na naturalną mowę, `literal` czyta składnię znak po znaku, a `skip` pomija bloki kodu.
* **`AudioFormat`**: Określa format docelowego pliku dźwiękowego.

---

## 2. Niezmienne obiekty wartości

### `AudioSpec`

Definiuje parametry akustyczne próbkowania dźwięku:

```python
@dataclass(frozen=True)
class AudioSpec:
    sample_rate: int = 24000
    channels: int = 1
    sample_width: int = 2  # 16-bitowe PCM
    format: AudioFormat = "wav"

```

### `SpeechSegment`

Reprezentuje niepodzielny fragment wypowiedzi przygotowany do syntezy neuronowej:

```python
@dataclass(frozen=True)
class SpeechSegment:
    text: str
    lang: str = "pl"
    pause_after_ms: int = 300
    is_code: bool = False
    rate: float = 1.0

```

* **`text`**: W pełni znormalizowany ciąg znaków oczyszczony fonetycznie.
* **`lang`**: Kod języka lektora (`pl` lub `en`).
* **`pause_after_ms`**: Długość ciszy w milisekundach dodawanej po segmencie (np. 300 ms po zdaniu, 650 ms po bloku kodu, 800 ms po nagłówku).
* **`is_code`**: Flaga informująca, czy segment pochodzi z kodu źródłowego.

---

## 3. Bufory audio i encje wynikowe

### `AudioBuffer`

Hermetyzuje tablicę jednowymiarową 32-bitowych próbek zmiennoprzecinkowych PCM (NumPy `float32`):

```python
class AudioBuffer:
    def __init__(self, data: np.ndarray) -> None:
        if data.dtype != np.float32:
            data = data.astype(np.float32)
        self._data = data

    @property
    def data(self) -> np.ndarray:
        return self._data

    @property
    def duration_sec(self) -> float:
        return len(self._data) / 24000.0

```

### `SynthesisResult` i `SynthesisStats`

Przekazuje podsumowanie wykonania syntezy, metryki czasu trwania oraz liczbę trafień w pamięć podręczną:

```python
@dataclass(frozen=True)
class SynthesisStats:
    total_segments: int
    cached_segments: int
    synthesized_segments: int
    duration_sec: float
    elapsed_sec: float
    realtime_factor: float

@dataclass(frozen=True)
class SynthesisResult:
    audio_path: Path
    stats: SynthesisStats
    skipped_existing: bool = False

```