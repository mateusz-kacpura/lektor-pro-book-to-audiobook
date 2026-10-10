# Reguły biznesowe: synteza audio i pamięć podręczna (BR-016 do BR-020)

## Przegląd

Niniejsze reguły określają standardy generowania mowy, łączenia segmentów audio, cyfrowego przetwarzania sygnałów (DSP) oraz deterministycznej pamięci podręcznej.

---

### BR-016: Deterministyczny cache audio adresowany zawartością

- **Treść reguły**: Wygenerowane segmenty mowy muszą być buforowane przy użyciu deterministycznego skrótu SHA-256 wyliczanego z parametrów syntezy.
- **Niezmiennik**: Klucz pamięci podręcznej tworzony jest z krotki:
  $$\text{hasz} = \text{SHA256}(\text{znormalizowany\_tekst} \mathbin{\Vert} \text{język} \mathbin{\Vert} \text{głos} \mathbin{\Vert} \text{temperatura} \mathbin{\Vert} \text{cfg})$$
- **Układ dyskowy**: Pliki zapisywane są w dwuznakowych podkatalogach: `cache_dir/<hasz[:2]>/<hasz>.npy`.
- **Egzekwowanie**: Wdrożone w `AudioSegmentCache` w module `lektor.adapters.tts.cache`. Trafienie w pamięć podręczną zwraca bufor w czasie $0\text{ ms}$ bez obciążania karty graficznej.

---

### BR-017: Czteroetapowe oczyszczanie sygnału audio (potok DSP)

- **Treść reguły**: Każdy bufor mowy o długości przekraczającej 0,2 sekundy musi przejść przez czteroetapowy potok filtracji cyfrowej.
- **Niezmiennik**: Przetwarzanie przebiega w ściśle określonej kolejności:
  1. **Filtr górnoprzepustowy**: Filtr Butterwortha 4. rzędu z odcięciem na $75\text{ Hz}$ eliminujący dudnienie vocodera.
  2. **Przycinanie granic mowy**: Model Silero VAD pracujący na $16\text{ kHz}$ odcinający artefakty po wymuszonym tokenie końca zdania (z fallbackiem do energii RMS).
  3. **Spektralna redukcja szumów**: Usuwanie stacjonarnego szumu tła za pomocą biblioteki `noisereduce`.
  4. **Wygładzanie brzegów**: $15\text{ ms}$ liniowego wyciszenia narastającego (fade-in) oraz $35\text{ ms}$ cosinusowego wygaszania (fade-out, $\cos^2$).
- **Egzekwowanie**: Realizowane w klasie `SileroAudioCleaner` w module `lektor.adapters.audio.cleaner`.

---

### BR-018: Normalizacja poziomu głośności i ochrona przed przesterowaniem

- **Treść reguły**: Połączona ścieżka dźwiękowa musi zostać znormalizowana przed zapisem na dysk w celu zapobieżenia przesterowaniu cyfrowemu (clipping).
- **Niezmiennik**:
  $$\text{audio\_znormalizowane} = \left( \frac{\text{audio}}{\max(\vert{}\text{audio}\vert{})} \right) \times 0{,}95$$
  Szczytowa amplituda sygnału nie może przekroczyć wartości $0{,}95$ ($-0{,}45\text{ dBFS}$).
- **Egzekwowanie**: Wykonywane przez metodę `NumpyAudioStitcher.normalize_volume`.

---

### BR-019: Wzajemne wykluczanie modeli na karcie graficznej (arbiter VRAM)

- **Treść reguły**: Model wizyjny (`SLOT_VISION`) oraz syntezator mowy (`SLOT_AUDIO_TTS`) nie mogą jednocześnie zajmować pamięci karty graficznej o pojemności 12 GB VRAM.
- **Niezmiennik**: Wejście do `SLOT_AUDIO_TTS` wymusza wywłaszczenie: zamknięcie procesu `llama-server.exe`, oczekiwanie na zwolnienie pamięci i sprawdzenie zasobów. Wejście do `SLOT_VISION` zwalnia wagi PyTorch, uruchamia odśmiecacz pamięci i czyści bufor CUDA.
- **Egzekwowanie**: Zarządzane przez `DynamicVramModelArbiter.acquire` w module `lektor.adapters.resources.arbiter`.

---

### BR-020: Standardowy format eksportu plików audio

- **Treść reguły**: Wszystkie wynikowe nagrania stron książki oraz nagrania ze studia muszą być zapisywane jako 16-bitowe pliki WAV w formacie PCM z częstotliwością próbkowania $24\,000\text{ Hz}$.
- **Niezmiennik**: Parametry techniczne pliku wymagają: `sample_rate = 24000`, `subtype = PCM_16` oraz pojedynczego kanału mono.
- **Egzekwowanie**: Zdefiniowane w obiekcie wartości `AudioSpec` i egzekwowane w `NumpyAudioStitcher.save_audio`.
