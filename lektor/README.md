# Lektor — System Syntezy Mowy (TTS) dla Książek Technicznych

Program **Lektor** służy do automatycznej zamiany stron książek programistycznych (z formatu Markdown) na wysokiej jakości mowę z wykorzystaniem modelu **Chatterbox Multilingual**.

Pakiet wykonuje zaawansowaną **normalizację tekstu technicznego**, w tym:
- **Rozpoznawanie języka (Polski / Angielski)** — rozróżnia całe frazy angielskie (np. tytuły, cytaty) od tekstu polskiego.
- **Słownik fonetyczny i akronimów IT** — automatycznie transkrybuje trudne terminy programistyczne (np. *stateless*, *load balancer*, *goroutine*, *gRPC*, *K8s*, *CI/CD*).
- **Normalizację składni kodu i operatorów** — zamienia listingi i operatory (`:=`, `!=`, `err != nil`, `func`, `struct`, komentarze `//`) na naturalny język mówiony.
- **Normalizację liczb i rozdziałów** — konwertuje zapisy typu *Rozdział 9* $\rightarrow$ *Rozdział dziewiąty*, wersje *v1.2.0*, złożoność $O(n \log n)$ oraz procenty.
- **Składanie audio z naturalnymi pauzami** — łączy wygenerowane zdania, wstawiając odpowiednie przerwy między przecinkami, zdaniami, akapitami i nagłówkami.

---

## 📁 Struktura Projektu (Czysta Architektura)

```text
lektor/
│
├── domain/                      # 1. WARSTWA DOMENOWA (Entities & Value Objects)
│   ├── models.py                # SpeechSegment, AudioSpec, SynthesisStats, Book
│   ├── normalization.py         # Usługa domenowa TextNormalizationService
│   └── normalizers/             # Reguły normalizacji (kod Go, liczebniki, Markdown, słownik)
│
├── application/                 # 2. WARSTWA APLIKACJI (Use Cases & Contracts)
│   ├── protocols.py             # Porty Wejścia/Wyjścia (DIP, bez Any)
│   ├── dtos.py                  # Command & Query DTO
│   └── use_cases/               # Przypadki użycia (SynthesizePage, BatchSynthesis, ConvertBook, PreviewPage)
│
├── adapters/                    # 3. WARSTWA ADAPTERÓW (Interface Adapters)
│   ├── cli/                     # Kontroler wiersza poleceń CLI
│   ├── storage/                 # Repozytorium stron i magazynu książek
│   ├── tts/                     # Adaptery silników TTS (Chatterbox, Mock, SystemVoice, Factory)
│   ├── audio/                   # Składanie próbek dźwiękowych (NumpyAudioStitcher)
│   ├── ocr/                     # Adaptery ekstrakcji OCR (Qwen2.5-VL:7B, Formatter)
│   └── gui/                     # Adapter serwera Web GUI (FastAPI)
│
├── infrastructure/              # 4. WARSTWA INFRASTRUKTURY (Frameworks & Drivers)
│   └── config.py                # Detekcja sprzętowa (GPU CUDA / CPU) i SSOT ścieżek
```


---

## 🚀 Sposób Użycia (CLI)

Głównym punktem wejścia jest plik `main.py`.

### 1. Podgląd znormalizowanego tekstu (Preview)
Pozwala sprawdzić, jak program znormalizował tekst, jakie wykrył języki i jak podzielił stronę na segmenty mowy:

```bash
# Podgląd strony 032
python main.py preview pages/page_032.md

# Podgląd strony z kodem programistycznym (page_047)
python main.py preview pages/page_047.md
```

Możesz wybrać tryb czytania bloków kodu:
- `--code-mode spoken` (domyślny) — czyta listingi linia po linii z komentarzami.
- `--code-mode summary` — czyta tylko podsumowanie (np. *"Listing w języku Go zawierający 8 linii"*).
- `--code-mode skip` — pomija bloki kodu.

### 2. Konwersja pojedynczej strony na plik audio (Single)
```bash
# Synteza mowy z modelem Chatterbox Multilingual:
python main.py single pages/page_032.md -o audio_output

# Dostrajanie próbkowania (eliminacja halucynacji i mruczenia):
python main.py single pages/page_032.md --temp 0.35 --cfg 0.7 --exaggeration 0.25

# Z próbką głosu (voice cloning / speaker reference):
python main.py single pages/page_032.md --voice glos_lektora.wav

# Szybki test offline (SystemVoice / Paulina + Zira):
python main.py single pages/page_032.md --mock
```

Wyjściowy plik `.wav` oraz plik tekstowy z transkrypcją `page_032_normalized.txt` trafią do katalogu `audio_output/`. Po zakończeniu syntezy program wyświetla szczegółowe **statystyki wydajności i prędkości generowania dźwięku**:
- **Czas generowania** (w sekundach),
- **Długość audio** (mm:ss),
- **Współczynnik RTF** (Real-Time Factor: stosunek czasu generowania do długości mowy),
- **Prędkość względem czasu rzeczywistego** (np. `0.9x – 4.5x`),
- **Przepustowość tekstu** (znaków/s oraz słów/s),
- **Średni czas syntezy segmentu**.

### 3. Konwersja wsadowa całej książki (Batch)
Aby przekonwertować wszystkie 161 stron z katalogu `pages/`:

```bash
python main.py batch pages/ --pattern "page_*.md" -o audio_output
```

---

## ⚙️ Konfiguracja Chatterbox Multilingual

W pliku `lektor/infrastructure/config.py` lub jako parametry CLI możesz dostosować:
- `model_name_or_path`: ścieżka do lokalnego folderu z wagami lub identyfikator modelu HuggingFace.
- `reference_voice_path`: plik `.wav` z głosem lektora (dla klonowania głosu).
- `pause_sentence_ms`: długość pauzy po zdaniu (domyślnie `350 ms`).
- `pause_paragraph_ms`: długość pauzy po akapicie (domyślnie `650 ms`).
- `pause_header_ms`: pauza po nagłówku sekcji (domyślnie `800 ms`).
- `device`: automatycznie wykrywa kartę graficzną NVIDIA CUDA lub CPU.
