# Topologia wdrożenia (poziom 4)

## Przegląd

Diagram wdrożenia przedstawia fizyczną topologię uruchomieniową platformy na lokalnej stacji roboczej wyposażonej w kartę graficzną NVIDIA.

```mermaid
C4Deployment
    title Diagram wdrożenia - lokalna topologia sprzętowa

    Deployment_Node(workstation, "Stacja robocza inżyniera", "Windows 11 x64, 12 rdzeni CPU, 32 GB RAM") {
        Deployment_Node(gpuHardware, "Karta graficzna", "NVIDIA GeForce RTX 3060 12 GB VRAM") {
            Container(cudaCores, "Rdzenie CUDA", "Środowisko CUDA 12.x", "Wykonuje operacje tensorowe i obliczenia macierzowe modeli neuronowych.")
        }

        Deployment_Node(pyRuntime, "Środowisko uruchomieniowe Python", "Python 3.14.x x64") {
            Container(fastapiProc, "Proces FastAPI / Uvicorn", "Główny proces / port 7860", "Obsługuje serwer aplikacji, routery GUI, wątki robocze i strumień SSE.")
            Container(forwarderProc, "Proces forwardera TCP", "Proces potomny / port 80", "Przekazuje asynchronicznie ruch z portu 80 na 7860 przez pętlę zwrotną.")
            Container(pytorchEngine, "Silnik PyTorch", "Biblioteki DLL w procesie", "Ładuje wagi modeli OmniVoice/Chatterbox do pamięci karty graficznej.")
        }

        Deployment_Node(cppRuntime, "Środowisko llama.cpp", "Wersja binarna Win-x86_64 AVX2 CUDA 12") {
            Container(llamaProc, "Proces llama-server.exe", "Proces potomny / port 1234", "Hostuje model Gemma 4 12B GGUF z projektorem wizyjnym BF16.")
        }

        Deployment_Node(storageDisk, "Dysk półprzewodnikowy NVMe SSD", "System plików NTFS") {
            ContainerDb(projectData, "Magazyn danych projektu", "./data", "Zawiera katalogi books/, audio_book/, cache/ oraz plik konfiguracyjny .env.")
        }

        Deployment_Node(clientBrowser, "Środowisko przeglądarki", "Google Chrome / Microsoft Edge") {
            Container(browserUi, "Kontekst przeglądarki", "Silnik Chromium", "Wykonuje odtwarzacz audio, kontrolery UI i renderuje elementy DOM.")
        }
    }

    Rel(browserUi, forwarderProc, "Wysyła żądania bez podawania portu", "HTTP / port 80")
    Rel(forwarderProc, fastapiProc, "Przekierowuje pakiety TCP", "Pętla zwrotna TCP / port 7860")
    Rel(browserUi, fastapiProc, "Pobiera zasoby statyczne, wywołuje API i nasłuchuje SSE", "HTTP REST / port 7860")
    Rel(fastapiProc, llamaProc, "Zarządza procesem potomnym i wysyła zapytania inferencji", "HTTP / port 1234")
    Rel(fastapiProc, pytorchEngine, "Wywołuje syntezę mowy przez API Pythona", "Wywołanie wewnątrzprocesowe")
    Rel(pytorchEngine, cudaCores, "Alokuje tensory w pamięci VRAM (~2.5-3.5 GB)", "CUDA API")
    Rel(llamaProc, cudaCores, "Zajmuje warstwy w pamięci VRAM (~7.5-8.5 GB)", "Sterownik CUDA API")
    Rel(fastapiProc, projectData, "Zapisuje pliki WAV, dokumenty Markdown i metadane JSON", "Win32 operacje wejścia/wyjścia")

```

## Alokacja procesów i zasobów

* **Główny proces FastAPI / Uvicorn (port 7860)**: Odpowiada za wykonywanie przypadków użycia, koordynację wątków roboczych `threading.Thread` oraz zapis plików.
* **Proces forwardera TCP (port 80)**: Umożliwia dostęp do interfejsu w sieci lokalnej bez konieczności wpisywania numeru portu w przeglądarce.
* **Proces serwera multimodalnego (`llama-server.exe`, port 1234)**: Uruchamiany automatycznie przez `ProcessModelHandle` przy wejściu do slotu `SLOT_VISION`. Jest bezpiecznie zamykany przed rozpoczęciem syntezy mowy.
* **Wewnątrzprocesowy silnik PyTorch**: Ładowany przez `PyTorchModelHandle` w slocie `SLOT_AUDIO_TTS`. Pamięć jest jawnie zwalniana za pomocą odśmiecacza pamięci i czyszczenia pamięci podręcznej CUDA.
* **Ograniczenia pamięci GPU**: Ze względu na fizyczny limit 12 GB pamięci VRAM, jednoczesne utrzymanie obu modeli doprowadziłoby do błędu braku pamięci (OOM). Topologia wdrożenia opiera się na sekwencyjnym wywłaszczaniu zasobów na poziomie systemu operacyjnego.
