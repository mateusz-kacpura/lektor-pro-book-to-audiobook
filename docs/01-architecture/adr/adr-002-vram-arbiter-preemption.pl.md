# ADR-002: Dynamiczny arbiter pamięci VRAM i wywłaszczanie zasobów sprzętowych

## Kontekst
Karty graficzne z 12 GB pamięci VRAM (np. NVIDIA GeForce RTX 3060) nie są w stanie utrzymać jednocześnie dużego multimodalnego modelu wizyjnego (Gemma 4 12B w kwantyzacji Q4_K_M zajmującego ~7.5 GB VRAM) oraz neuronowego syntezatora mowy (OmniVoice / Chatterbox zajmującego ~2.5–3.5 GB VRAM wraz ze strukturami PyTorch). Współbieżna alokacja obu modeli prowadzi do natychmiastowego błędu braku pamięci (`CUDA out of memory`).

## Decyzja
Wprowadzono centralny mechanizm arbitrażu zasobów sprzętowych oparty na wzajemnym wykluczaniu: `DynamicVramModelArbiter` (`lektor.adapters.resources.arbiter`).
- Modele przypisane są do dedykowanych slotów: `SLOT_VISION` (`vision_ocr`) oraz `SLOT_AUDIO_TTS` (`audio_tts`).
- Przed rozpoczęciem analizy wizyjnej arbiter wywłaszcza model syntezy mowy: usuwa instancję z pamięci, wywołuje odśmiecacz (`gc.collect()`), zwalnia bufory CUDA (`torch.cuda.empty_cache()`) oraz czyści pamięć międzyprocesową (`torch.cuda.ipc_collect()`).
- Przed rozpoczęciem syntezy mowy arbiter wywłaszcza proces serwera wizyjnego (`llama-server.exe`): zamyka proces systemowy i oczekuje na zwolnienie pamięci karty przed alokacją wag PyTorch.
- Przypadki użycia rezerwują zasób za pomocą metody `acquire()` lub menedżera kontekstu.

## Konsekwencje
- **Pozytywne:**
  - Całkowita eliminacja błędów CUDA OOM na kartach konsumenckich.
  - Możliwość wykorzystania pełnych możliwości modeli bez sztucznego obcinania kontekstu.
- **Negatywne:**
  - Przełączenie slotu wiąże się z narzutem czasowym rzędu 1.5–3.5 sekundy na zwolnienie i załadowanie wag.
