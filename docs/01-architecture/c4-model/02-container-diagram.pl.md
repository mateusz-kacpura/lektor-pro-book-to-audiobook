# Diagram kontenerów (poziom 2)

## Przegląd

Diagram kontenerów ilustruje podział systemu Lektor Pro na jednostki wykonawcze, użyte technologie oraz komunikację międzyprocesową.

```mermaid
flowchart TB
    classDef person fill:#08427b,stroke:#073b6f,color:#fff,stroke-width:2px;
    classDef container fill:#1168bd,stroke:#0b4884,color:#fff,stroke-width:2px;
    classDef storage fill:#5a6268,stroke:#343a40,color:#fff,stroke-width:2px;
    classDef extProcess fill:#6c757d,stroke:#495057,color:#fff,stroke-width:2px;

    user["👤 <b>Użytkownik / czytelnik</b><br/><i>[Osoba]</i><br/><br/>Korzysta z aplikacji przez przeglądarkę internetową lub terminal."]:::person

    subgraph LektorEnv [" 🏛️ Środowisko wykonawcze Lektor Pro "]
        direction TB

        subgraph IngressGroup [" Punkty wejścia klienta "]
            direction LR
            browser["🌐 <b>Interfejs Web GUI</b><br/><i>[Vanilla JS, moduły ES, HTML5, CSS3]</i><br/><br/>Pulpit roboczy w przeglądarce: odtwarzacz audio,<br/>czytnik Markdown, notatnik i telemetria SSE."]:::container
            cli["💻 <b>Interfejs konsolowy CLI</b><br/><i>[Python 3.14 / argparse]</i><br/><br/>Narzędzia wiersza poleceń do syntezy wsadowej,<br/>zarządzania katalogiem i konwersji skanów."]:::container
            portFwd["🔀 <b>Forwarder TCP</b><br/><i>[Python 3.14 / asyncio]</i><br/><br/>Przekierowuje ruch z portu 80 na wewnętrzny port 7860<br/>dla bezpośredniego dostępu w sieci LAN i Tailscale."]:::container
        end

        webServer["⚡ <b>Serwer aplikacji</b><br/><i>[Python 3.14 / FastAPI i Uvicorn]</i><br/><br/>Udostępnia punkty REST, strumieniowanie SSE,<br/>serwowanie zasobów i wstrzykiwanie zależności."]:::container

        appCore["⚙️ <b>Rdzeń aplikacji i przypadki użycia</b><br/><i>[Python 3.14 (ścisłe typowanie bez Any)]</i><br/><br/>Modele domenowe, normalizatory lingwistyczne,<br/>potoki zadań oraz kontrakty portów."]:::container

        subgraph ProcessingGroup [" Podsystemy audio i zasobów sprzętowych "]
            direction LR
            audioEngine["🎵 <b>Podsystem audio DSP i TTS</b><br/><i>[NumPy, SciPy, SoundFile, PyTorch, Silero VAD]</i><br/><br/>Synteza mowy, buforowanie bez alokacji,<br/>filtry odszumiania i pamięć podręczna SHA-256."]:::container
            vramArbiter["🛡️ <b>Dynamiczny arbiter VRAM</b><br/><i>[Procesy potomne / PyTorch CUDA API]</i><br/><br/>Zapewnia wzajemne wykluczanie na GPU,<br/>wywłaszczając llama-server przed załadowaniem TTS."]:::container
        end
    end

    subgraph ExternalGroup [" Pamięć masowa i procesy zewnętrzne "]
        direction LR
        fs[("💾 <b>Lokalny system plików</b><br/><i>[Magazyn dyskowy stacji roboczej]</i><br/><br/>Katalogi data/books/<slug>/, skany stron,<br/>pliki WAV, notatki oraz konfiguracja .env.")]:::storage
        llamaServer["🧠 <b>Serwer multimodalny VLM</b><br/><i>[llama-server.exe (C++ / CUDA)]</i><br/><br/>Hostuje modele Gemma 4 lub Qwen z projektorem<br/>wizyjnym mmproj na porcie 1234."]:::extProcess
    end

    user -->|"Obsługuje pulpit GUI<br/><b>[HTTP]</b>"| browser
    user -->|"Uruchamia przetwarzanie<br/><b>[Powłoka CLI]</b>"| cli
    user -->|"Wysyła żądania na port 80<br/><b>[TCP:80]</b>"| portFwd

    portFwd -->|"Przekazuje ruch na port 7860<br/><b>[TCP pętla zwrotna]</b>"| webServer
    browser -->|"Wywołuje REST API i nasłuchuje SSE<br/><b>[HTTP REST / SSE]</b>"| webServer
    cli -->|"Wywołuje przypadki użycia bezpośrednio<br/><b>[Wywołania metod]</b>"| appCore
    webServer -->|"Deleguje żądania HTTP do use case'ów<br/><b>[FastAPI Depends]</b>"| appCore

    appCore -->|"Zleca syntezę mowy i czyszczenie audio<br/><b>[Porty audio]</b>"| audioEngine
    appCore -->|"Żąda dostępu do slotu (SLOT_VISION / SLOT_AUDIO_TTS)<br/><b>[Porty zasobów]</b>"| vramArbiter
    appCore -->|"Odczytuje i zapisuje strony oraz pliki WAV<br/><b>[Porty magazynów / I/O]</b>"| fs
    appCore -->|"Przesyła skany stron w celu ekstrakcji<br/><b>[HTTP REST / Port 1234]</b>"| llamaServer

    vramArbiter -.->|"Uruchamia, monitoruje i zamyka proces<br/><b>[Proces potomny / Sygnały]</b>"| llamaServer
```

## Kontenery systemu

1. **Interfejs przeglądarkowy Web GUI**: Zbudowany w czystym JavaScripcie (moduły ES) bez frameworków SPA. Odpowiada za odtwarzanie dźwięku, synchronizację z systemem oraz zarządzanie oknami pulpitu.
2. **Serwer aplikacji (FastAPI)**: Udostępnia punkty końcowe REST, zarządza wątkami roboczymi `threading.Thread` i strumieniuje telemetrię postępu przez `SseTelemetryBroadcasterAdapter`.
3. **Forwarder TCP**: Lekki serwer asynchroniczny `asyncio` pozwalający na dostęp do systemu pod portem 80 obok portu 7860.
4. **Rdzeń aplikacji i przypadki użycia**: Usługi domenowe i interaktory operujące wyłącznie na abstrakcjach portów ze ścisłą kontrolą typów.
5. **Podsystem audio DSP i TTS**: Łączy neuronową generację mowy z filtrami cyfrowego przetwarzania sygnałów i pamięcią podręczną adresowaną haszem SHA-256.
6. **Dynamiczny arbiter VRAM**: Kontroluje obecność modeli w pamięci karty graficznej, eliminując błędy braku pamięci (OOM).

---

## ⚙️ Specyfikacja techniczna kontenerów

| Kontener | Stos technologiczny | Interfejs / Port | Główna odpowiedzialność |
| --- | --- | --- | --- |
| **Web GUI Frontend** | Vanilla JS (ESM), CSS3, HTML5 | DOM przeglądarki | Menedżer okien pulpitu, odtwarzacz audio, czytnik Markdown i nasłuchiwanie SSE. |
| **Forwarder TCP** | Python `asyncio` (`port_forwarder.py`) | TCP `0.0.0.0:80` $\to$ `127.0.0.1:7860` | Dostęp w sieci lokalnej bez konieczności podawania portu w przeglądarkach mobilnych. |
| **Serwer aplikacji API** | FastAPI, Uvicorn, Python 3.14 | HTTP `127.0.0.1:7860` | Punkty końcowe REST, walidacja Pydantic i zarządzanie wątkami roboczymi. |
| **Konsola CLI** | Python `argparse` (`main.py`) | CLI powłoki | Wsadowe potoki przetwarzania i syntezy w środowiskach bez interfejsu graficznego. |
| **Arbiter zasobów VRAM** | Python (`DynamicVramModelArbiter`) | Protokół wewnętrzny | Wywłaszczanie modeli na karcie graficznej w celu uniknięcia błędów OOM. |
| **Silnik wizyjny AI** | `llama-server.exe` (CUDA 12) | HTTP `127.0.0.1:1234/v1` | Multimodalny OCR skanów i tłumaczenie techniczne na polski Markdown. |
| **Silnik TTS i DSP** | PyTorch, SciPy, NumPy, SoundFile | Biblioteki w procesie | Synteza mowy, odszumianie Silero VAD i normalizacja głośności. |
| **Magazyn plików** | System plików systemu operacyjnego | Hierarchia katalogów | Przechowywanie skanów 300 DPI, wygenerowanych plików Markdown i ścieżek WAV. |
