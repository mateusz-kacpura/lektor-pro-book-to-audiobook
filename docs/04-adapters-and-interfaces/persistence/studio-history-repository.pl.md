# Repozytorium historii studia nagrań

## Przegląd

Adapter `FileSystemStudioHistoryRepository` (`lektor.adapters.storage.studio_repository`) realizuje kontrakt `StudioHistoryRepositoryProtocol`. Zapewnia trwały zapis metadanych nagrań z modułu Markdown TTS Studio oraz synchronizuje stan bazy JSON z rzeczywistymi plikami WAV na dysku.

---

## 1. Struktura zapisu danych

- **Indeks metadanych**: `data/audio_book/studio/history.json`
- **Pliki dźwiękowe**: `data/audio_book/studio/<id>.wav`

```json
[
  {
    "id": "tts_1791542400_a1b2c3",
    "title": "Architektura Cloud Native",
    "markdown": "# Architektura Cloud Native...",
    "normalized_preview": "Wstęp do architektury chmurowej...",
    "segments_count": 8,
    "lang": "bilingual",
    "speed": 1.0,
    "filename": "tts_1791542400_a1b2c3.wav",
    "audio_url": "/audio/studio/tts_1791542400_a1b2c3.wav",
    "audio_exists": true,
    "duration_sec": 42.5,
    "file_size_kb": 2040.0,
    "synth_time_sec": 3.12,
    "created_at": "2026-10-09 11:45:00"
  }
]

```

---

## 2. Synchronizacja z plikami na dysku

* `get_history()`: Wczytuje wpisy z pliku `history.json` i sprawdza fizyczną obecność pliku `.wav` na dysku, aktualizując flagę `audio_exists`.
* `add_or_update_item(item)`: Dodaje nowe nagranie na początek listy historii i zapisuje zaktualizowany stan do pliku JSON.
* `delete_item(item_id)`: Usuwa wpis z pliku `history.json` oraz trwale kasuje powiązany plik dźwiękowy (`<id>.wav`) z dysku.
