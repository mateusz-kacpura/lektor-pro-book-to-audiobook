# Specyfikacja modeli syntezy mowy (OmniVoice i Chatterbox)

## Przegląd

Dokument zawiera specyfikację techniczną modeli neuronowej syntezy mowy obsługiwanych przez platformę Lektor Pro. Wykonywane przez `UniversalTTSEngine` (`lektor.adapters.tts.universal_engine`), modele te umożliwiają klonowanie głosu w trybie zero-shot, dwujęzyczne przełączanie akcentów oraz naturalną kadencję lektorską.

---

## 1. Zestawienie porównawcze modeli

| Parametr | k2-fsa / OmniVoice (Domyślny) | Resemble AI / Chatterbox |
| :--- | :--- | :--- |
| **Identyfikator modelu** | `k2-fsa/OmniVoice` | `ResembleAI/chatterbox` |
| **Architektura** | Flow matching transformer + vocoder neuronowy | Model autoregresyjny + dyfuzja |
| **Zajętość pamięci VRAM** | ~2,5 do 3,2 GB | ~3,0 do 3,8 GB |
| **Częstotliwość próbkowania** | 24 000 Hz | 24 000 Hz |
| **Obsługa języków** | 600+ języków (płynny PL i EN) | Wielojęzyczny |
| **Klonowanie głosu** | Zero-shot z pojedynczego pliku referencyjnego | Kondycjonowanie próbką audio |
| **Przepustowość inferencji** | Współczynnik RTF ~0,12 - 0,20 na RTX 3060 | Współczynnik RTF ~0,25 - 0,40 |

---

## 2. Parametry i hiperparametry syntezy

Zarządzane przez `SynthesisConfig` w module `lektor.domain.audio_models`:

- **Temperatura (`temperature = 0.33`)**: Określa wariancję intonacji. Niższa wartość eliminuje zniekształcenia głosu i niekontrolowane spadki tonu przy terminach technicznych.
- **Waga CFG (`cfg_weight = 0.68`)**: Steruje siłą trzymania się fonetyki tekstu względem swobody vocodera.
- **Ekspresja (`exaggeration = 0.25`)**: Poziom emocjonalności mowy. Niski parametr zapewnia spokojny, wyważony ton audiobooka technicznego.
- **Kara za powtórzenia (`repetition_penalty = 1.8`)**: Chroni przed zacięciami i zapętleniami na znakach interpunkcyjnych.

---

## 3. Wymagania sprzętowe

- **Karta graficzna**: Akcelerator zgodny z CUDA 12.x z minimum 4 GB wolnej pamięci VRAM.
- **Tryb awaryjny**: Automatyczny fallback do wielowątkowego przetwarzania CPU w precyzji float32 w przypadku braku karty graficznej.