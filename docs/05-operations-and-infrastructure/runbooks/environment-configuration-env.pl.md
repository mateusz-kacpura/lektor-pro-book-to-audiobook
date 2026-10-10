# Instrukcja konfiguracji środowiska (.env)

## Przegląd

Platforma Lektor Pro wykorzystuje zmienne środowiskowe ładowane z pliku `.env` przez funkcję `load_env_file()` w module `lektor.infrastructure.config` jako pojedyncze źródło prawdy (SSOT). Dokument opisuje wszystkie dostępne zmienne, ich wartości domyślne oraz wpływ architektoniczny na działanie systemu.

---

## 1. Wykaz zmiennych środowiskowych

| Zmienna środowiskowa | Wartość domyślna | Dopuszczalne wartości | Opis i znaczenie architektoniczne |
| :--- | :--- | :--- | :--- |
| `LEKTOR_DATA_DIR` | `data` | Ścieżka do katalogu | Główny katalog danych. Określa ścieżki w obiekcie `DataPaths.from_data_dir()`. |
| `LEKTOR_ACTIVE_BOOK` | `cloud_native_go` | Poprawny slug książki | Identyfikator aktywnej książki w katalogu `data/books/<slug>/`. Fallback przy braku pliku `.active`. |
| `LEKTOR_DEVICE` | `auto` | `auto`, `cuda`, `cpu` | Urządzenie obliczeniowe. Wartość `auto` sprawdza dostępność CUDA przez `torch.cuda.is_available()`. |
| `LEKTOR_GUI_HOST` | `127.0.0.1` | Adres IP / hostname | Interfejs sieciowy, na którym nasłuchuje serwer FastAPI / Uvicorn. |
| `LEKTOR_GUI_PORT` | `7860` | Port TCP (np. `7860`) | Port serwera Web GUI. |
| `LEKTOR_AUTO_OPEN_BROWSER`| `true` | `true`, `false` | Automatyczne otwieranie przeglądarki po uruchomieniu skryptu `run_gui.py`. |
| `LEKTOR_TTS_ENGINE` | `omnivoice` | `omnivoice`, `chatterbox`, `mock` | Domyślny silnik syntezy wybierany przez fabrykę `TTSEngineFactory`. |
| `LEKTOR_OMNIVOICE_MODEL` | `k2-fsa/OmniVoice` | Identyfikator / ścieżka | Wagi modelu OmniVoice do wielojęzycznej syntezy mowy. |
| `LEKTOR_CHATTERBOX_MODEL` | `ResembleAI/chatterbox`| Identyfikator / ścieżka | Identyfikator modelu Resemble AI Chatterbox. |
| `LEKTOR_VISION_MODEL` | `google/gemma-4-12b` | Tag modelu | Nazwa modelu przekazywana w nagłówku zapytania do endpointu wizyjnego. |
| `LEKTOR_VISION_API_URL` | `http://127.0.0.1:1234/v1` | Adres URL | Adres docelowy zapytań OpenAI Chat Completions dla analizy wizyjnej. |
| `LEKTOR_LLAMA_SERVER_BINARY`| `.../llama-server.exe` | Ścieżka do pliku `.exe`| Bezwzględna ścieżka do pliku wykonywalnego serwera `llama-server.exe`. |
| `LEKTOR_LLAMA_MODEL_PATH` | `.../gemma-4-12B-it-Q4_K_M.gguf` | Ścieżka do pliku | Wagi modelu w formacie GGUF ładowane przez proces wizyjny. |
| `LEKTOR_LLAMA_MMPROJ_PATH`| `.../mmproj-BF16.gguf` | Ścieżka do pliku | Wagi projektora multimodalnego (osadzanie tokenów obrazu). |
| `LEKTOR_LLAMA_SERVER_PORT`| `1234` | Port TCP | Port dedykowany dla procesu `llama-server.exe`. |

---

## 2. Reguły ładowania konfiguracji

1. **Hierarchia pierwszeństwa**:
   $$\text{Zmienne środowiskowe systemu} > \text{Plik .env} > \text{Wartości domyślne w InfrastructureSettings}$$
2. **Parser bez bibliotek zewnętrznych**: Funkcja `load_env_file()` usuwa białe znaki i komentarze bez użycia pakietu `python-dotenv`. Istniejące zmienne procesu nie są nadpisywane.
3. **Niezmienność struktury DataPaths**: Utworzona instancja `DataPaths` jest zamrożonym obiektem wartości (`frozen=True`). Zmiana aktywnej książki wymaga wywołania `ApplicationContainer.reset_book_context()`.