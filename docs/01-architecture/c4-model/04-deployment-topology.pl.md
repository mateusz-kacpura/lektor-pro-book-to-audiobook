# Topologia wdrożenia (poziom 4)

## Przegląd

Diagram wdrożenia przedstawia fizyczną topologię uruchomieniową platformy na lokalnej stacji roboczej wyposażonej w kartę graficzną NVIDIA.

```mermaid
flowchart TB
    classDef hardware fill:#2d3748,stroke:#1a202c,color:#fff,stroke-width:2px;
    classDef process fill:#1168bd,stroke:#0b4884,color:#fff,stroke-width:2px;
    classDef runtime fill:#4361ee,stroke:#3a0ca3,color:#fff,stroke-width:2px;
    classDef storage fill:#5a6268,stroke:#343a40,color:#fff,stroke-width:2px;
    classDef client fill:#08427b,stroke:#073b6f,color:#fff,stroke-width:2px;

    subgraph Workstation [" 🖥️ Stacja robocza inżyniera (Windows 11 x64, 12 rdzeni CPU, 32 GB RAM) "]
        direction TB

        subgraph ClientGroup [" Środowisko klienta (Chromium) "]
            browserUi["🌐 <b>Kontekst przeglądarki</b><br/><i>[Google Chrome / Microsoft Edge]</i><br/><br/>Odtwarzacz audio, kontrolery UI i renderowanie DOM."]:::client
        end

        subgraph HostNetworking [" Warstwa sieciowa i serwer aplikacji "]
            forwarderProc["🔀 <b>Proces forwardera TCP</b><br/><i>[Python 3.14 / asyncio / Port 80]</i><br/><br/>Asynchroniczny nasłuch i przekierowanie do portu 7860."]:::process
            fastapiProc["⚡ <b>Główny proces FastAPI / Uvicorn</b><br/><i>[Python 3.14 x64 / Port 7860]</i><br/><br/>Serwer REST API, routery GUI, wątki robocze i telemetria SSE."]:::process
        end

        subgraph PythonEnv [" Środowisko Pythona i biblioteki TTS "]
            pytorchEngine["🎙️ <b>Wewnątrzprocesowy silnik PyTorch</b><br/><i>[DLL w pamięci procesu FastAPI]</i><br/><br/>Ładuje wagi modeli OmniVoice/Chatterbox do VRAM."]:::runtime
        end

        subgraph LlamaEnv [" Środowisko llama.cpp (Proces potomny) "]
            llamaProc["🧠 <b>Proces llama-server.exe</b><br/><i>[Binarny Win-x86_64 AVX2 CUDA 12 / Port 1234]</i><br/><br/>Hostuje model Gemma 4 12B GGUF z projektorem mmproj."]:::process
        end

        subgraph HardwareGroup [" Fizyczne zasoby sprzętowe i pamięć masowa "]
            direction LR
            cudaCores["⚡ <b>Karta graficzna NVIDIA RTX 3060 (12 GB VRAM)</b><br/><i>[Środowisko CUDA 12.x / Rdzenie Tensor]</i><br/><br/>Współdzielona pamięć: inferencja VLM (~8 GB) lub synteza TTS (~3 GB)."]:::hardware
            projectData[("💾 <b>Dysk NVMe SSD (System plików NTFS)</b><br/><i>[Lokalny magazyn ./data]</i><br/><br/>Katalogi books/, audio_book/, cache/ oraz plik .env.")]:::storage
        end
    end

    browserUi -->|"Żądanie bez numeru portu<br/><b>[HTTP / Port 80]</b>"| forwarderProc
    browserUi -->|"Pobieranie zasobów i API<br/><b>[HTTP REST / SSE / Port 7860]</b>"| fastapiProc
    forwarderProc -->|"Pętla zwrotna TCP<br/><b>[127.0.0.1:7860]</b>"| fastapiProc

    fastapiProc -->|"Zarządzanie procesem i zapytania<br/><b>[Subprocess / HTTP 1234]</b>"| llamaProc
    fastapiProc -->|"Wywołanie syntezy mowy<br/><b>[In-Process Call]</b>"| pytorchEngine
    fastapiProc -->|"Zapis plików WAV, Markdown i JSON<br/><b>[Win32 File I/O]</b>"| projectData

    pytorchEngine -->|"Alokuje tensory TTS w VRAM (~3 GB)<br/><b>[CUDA API]</b>"| cudaCores
    llamaProc -->|"Zajmuje pamięć VRAM (~8 GB)<br/><b>[CUDA Driver API]</b>"| cudaCores
```

## Alokacja procesów i zasobów

* **Główny proces FastAPI / Uvicorn (port 7860)**: Odpowiada za wykonywanie przypadków użycia, koordynację wątków roboczych `threading.Thread` oraz zapis plików.
* **Proces forwardera TCP (port 80)**: Umożliwia dostęp do interfejsu w sieci lokalnej bez konieczności wpisywania numeru portu w przeglądarce.
* **Proces serwera multimodalnego (`llama-server.exe`, port 1234)**: Uruchamiany automatycznie przez `ProcessModelHandle` przy wejściu do slotu `SLOT_VISION`. Jest bezpiecznie zamykany przed rozpoczęciem syntezy mowy.
* **Wewnątrzprocesowy silnik PyTorch**: Ładowany przez `PyTorchModelHandle` w slocie `SLOT_AUDIO_TTS`. Pamięć jest jawnie zwalniana za pomocą odśmiecacza pamięci i czyszczenia pamięci podręcznej CUDA.
* **Ograniczenia pamięci GPU**: Ze względu na fizyczny limit 12 GB pamięci VRAM, jednoczesne utrzymanie obu modeli doprowadziłoby do błędu braku pamięci (OOM). Topologia wdrożenia opiera się na sekwencyjnym wywłaszczaniu zasobów na poziomie systemu operacyjnego.
