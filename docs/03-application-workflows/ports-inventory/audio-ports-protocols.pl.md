# Porty i protokoły podsystemu audio

## Przegląd

Dokument zawiera specyfikację abstrakcyjnych kontraktów portów odpowiedzialnych za neuronową syntezę mowy, cyfrowe przetwarzanie sygnałów (DSP), łączenie próbek dźwiękowych, pamięć podręczną oraz wykrywanie głosów referencyjnych. Zdefiniowane w module `lektor.application.ports.audio_ports`, interfejsy te izolują przypadki użycia od konkretnych bibliotek audio.

---

## 1. `TTSEngineProtocol`

Określa kontrakt wymagany od silników syntezy mowy:

```python
class TTSEngineProtocol(Protocol):
    def load_model(self) -> None:
        """Ładuje wagi modelu neuronowego oraz vocodera do pamięci operacyjnej."""
        ...

    def unload_model(self) -> None:
        """Zwalnia model i alokacje pamięci VRAM z karty graficznej."""
        ...

    def synthesize_segment(self, text: str, lang: str = "pl") -> AudioBuffer:
        """Syntezuje pojedynczy znormalizowany segment tekstu na bufor AudioBuffer (float32)."""
        ...

    def is_loaded(self) -> bool:
        """Zwraca True, jeśli model jest zainicjalizowany i gotowy do inferencji."""
        ...

```

---

## 2. `AudioStitcherProtocol`

Odpowiada za konkatenację segmentów, dodawanie pauz, normalizację głośności oraz zapis plików:

```python
class AudioStitcherProtocol(Protocol):
    def stitch_segments(
        self,
        audio_segments: Sequence[tuple[AudioBuffer | Sequence[float], int]],
    ) -> AudioBuffer:
        """Łączy listę krotek (chunk_audio, pause_after_ms) w ciągły strumień dźwiękowy."""
        ...

    def normalize_volume(
        self,
        audio: AudioBuffer,
        target_peak: float = 0.95,
    ) -> AudioBuffer:
        """Normalizuje poziom głośności bufora próbek, zapobiegając przesterowaniu."""
        ...

    def create_silence(self, duration_ms: int) -> AudioBuffer:
        """Generuje bufor ciszy o określonej długości w milisekundach."""
        ...

    def save_audio(
        self,
        audio: AudioBuffer,
        output_path: Path,
        format: str = "wav",
    ) -> Path:
        """Zapisuje bufor audio do pliku na dysku."""
        ...

    def get_duration_sec(self, audio: AudioBuffer | Sequence[float]) -> float:
        """Oblicza czas trwania próbek w sekundach."""
        ...

    def audio_exists(self, output_path: Path, min_bytes: int = 0) -> bool:
        """Sprawdza, czy plik dźwiękowy istnieje i ma minimalny wymagany rozmiar."""
        ...

    def get_file_size_kb(self, output_path: Path) -> float:
        """Zwraca rozmiar pliku audio w kilobajtach."""
        ...

    def get_file_duration_sec(self, output_path: Path) -> float:
        """Zwraca czas trwania zapisanego pliku dźwiękowego w sekundach."""
        ...

```

---

## 3. `AudioCleanerProtocol`

Definiuje kontrakt usuwania szumów i artefaktów na krańcach wypowiedzi:

```python
class AudioCleanerProtocol(Protocol):
    def clean_tail(self, audio: AudioBuffer, sample_rate: int = 24000) -> AudioBuffer:
        """Czyści audio z artefaktów mowy, dudnienia vocodera i szumu tła (VAD i filtry DSP)."""
        ...

```

---

## 4. `AudioCacheProtocol`

Określa zachowanie pamięci podręcznej segmentów mowy adresowanej zawartością:

```python
class AudioCacheProtocol(Protocol):
    def get(
        self,
        text: str,
        lang: str = "pl",
        voice: Optional[str] = None,
        config: Optional[SynthesisConfig] = None,
        temperature: float = 0.35,
        cfg_weight: float = 0.7,
    ) -> Optional[AudioBuffer]:
        """Pobiera zbuforowaną tablicę audio lub zwraca None w przypadku braku trafienia."""
        ...

    def put(
        self,
        text: str,
        audio: AudioBuffer,
        lang: str = "pl",
        voice: Optional[str] = None,
        config: Optional[SynthesisConfig] = None,
        temperature: float = 0.35,
        cfg_weight: float = 0.7,
        sample_rate: int = 24000,
    ) -> None:
        """Zapisuje wygenerowane audio w pamięci podręcznej."""
        ...

```

---

## 5. `VoiceDiscoveryProtocol`

Udostępnia listę dostępnych próbek głosu lektora bez konieczności wpisywania ścieżek na stałe w kodzie:

```python
class VoiceDiscoveryProtocol(Protocol):
    def discover_voices(self) -> list[dict[str, str]]:
        """Zwraca listę dostępnych plików próbek głosu lektora."""
        ...

```