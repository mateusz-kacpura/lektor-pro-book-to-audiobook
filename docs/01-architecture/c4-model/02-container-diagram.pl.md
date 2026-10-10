# Diagram kontenerów (poziom 2)

## Przegląd

Diagram kontenerów ilustruje podział systemu Lektor Pro na jednostki wykonawcze, użyte technologie oraz komunikację międzyprocesową.

```mermaid
C4Container
    title Diagram kontenerów - Lektor Pro

    Person(user, "Użytkownik", "Korzysta z aplikacji przez przeglądarkę internetową lub terminal.")

    System_Boundary(c1, "Środowisko wykonawcze Lektor Pro") {
        Container(browser, "Interfejs przeglądarkowy Web GUI", "Vanilla JavaScript (moduły ES), HTML5 Audio, CSS3", "Pulpit roboczy w przeglądarce: odtwarzacz, czytnik Markdown, notatnik i telemetria na żywo.")
        Container(cli, "Interfejs konsolowy CLI", "Python 3.14 / argparse", "Narzędzia wiersza poleceń do syntezy wsadowej, zarządzania katalogiem książek i konwersji skanów.")
        Container(webServer, "Serwer aplikacji", "Python 3.14 / FastAPI i Uvicorn", "Punkty końcowe REST, strumieniowanie SSE, serwowanie plików statycznych i wstrzykiwanie zależności.")
        Container(portFwd, "Forwarder TCP", "Python 3.14 / asyncio", "Przekierowuje ruch z portu 80 na wewnętrzny port 7860 dla wygody w sieci lokalnej i Tailscale.")
        Container(appCore, "Rdzeń aplikacji i przypadki użycia", "Python 3.14 (ścisłe typowanie bez Any)", "Modele domenowe, normalizatory lingwistyczne, potoki zadań oraz kontrakty portów.")
        Container(audioEngine, "Podsystem audio DSP i TTS", "NumPy, SciPy, SoundFile, PyTorch, Silero VAD", "Synteza mowy, buforowanie bez alokacji, filtry odszumiania i pamięć podręczna SHA-256.")
        Container(vramArbiter, "Dynamiczny arbiter VRAM", "Procesy potomne / PyTorch CUDA API", "Zapewnia wzajemne wykluczanie na karcie graficznej, zamykając llama-server przed załadowaniem silnika TTS.")
    }

    ContainerDb(fs, "Lokalny system plików", "Magazyn dyskowy", "Katalogi data/books/<slug>/, skany, pliki WAV, notatki oraz konfiguracja .env.")
    Container_Ext(llamaServer, "Serwer multimodalny VLM", "llama-server.exe (C++ / CUDA)", "Udostępnia modele Gemma 4 lub Qwen z projektorem mmproj na porcie 1234.")

    Rel(user, browser, "Steruje odtwarzaniem, uruchamia konwersję, zapisuje notatki", "HTTP / przeglądarka")
    Rel(user, cli, "Uruchamia przetwarzanie wsadowe lub sprawdza status biblioteki", "Terminal / powłoka")
    Rel(browser, webServer, "Wywołuje REST API, pobiera pliki, nasłuchuje postępu", "HTTP REST / SSE")
    Rel(user, portFwd, "Wysyła żądania na port 80", "TCP")
    Rel(portFwd, webServer, "Przekazuje ruch na port 7860", "TCP pętla zwrotna")
    Rel(cli, appCore, "Wywołuje przypadki użycia bezpośrednio przez kontener", "Wywołania metod w pamięci")
    Rel(webServer, appCore, "Deleguje żądania HTTP do przypadków użycia przez Depends", "FastAPI Depends")
    Rel(appCore, audioEngine, "Zleca syntezę mowy, łączenie próbek i czyszczenie sygnału", "Porty audio")
    Rel(appCore, vramArbiter, "Żąda dostępu do slotu (SLOT_VISION lub SLOT_AUDIO_TTS)", "Porty zasobów")
    Rel(appCore, fs, "Odczytuje i zapisuje strony, pliki stanu oraz metadane", "Porty magazynów danych")
    Rel(vramArbiter, llamaServer, "Uruchamia, monitoruje i zamyka proces serwera przez taskkill", "Proces potomny / HTTP health check")
    Rel(appCore, llamaServer, "Przesyła skany stron w celu analizy i ekstrakcji", "HTTP REST / port 1234")

```

## Kontenery systemu

1. **Interfejs przeglądarkowy Web GUI**: Zbudowany w czystym JavaScripcie (moduły ES) bez frameworków SPA. Odpowiada za odtwarzanie dźwięku, synchronizację z systemem oraz zarządzanie oknami pulpitu.
2. **Serwer aplikacji (FastAPI)**: Udostępnia punkty końcowe REST, zarządza wątkami roboczymi `threading.Thread` i strumieniuje telemetrię postępu przez `SseTelemetryBroadcasterAdapter`.
3. **Forwarder TCP**: Lekki serwer asynchroniczny `asyncio` pozwalający na dostęp do systemu pod portem 80 obok portu 7860.
4. **Rdzeń aplikacji i przypadki użycia**: Usługi domenowe i interaktory operujące wyłącznie na abstrakcjach portów ze ścisłą kontrolą typów.
5. **Podsystem audio DSP i TTS**: Łączy neuronową generację mowy z filtrami cyfrowego przetwarzania sygnałów i pamięcią podręczną adresowaną haszem SHA-256.
6. **Dynamiczny arbiter VRAM**: Kontroluje obecność modeli w pamięci karty graficznej, eliminując błędy braku pamięci (OOM).
