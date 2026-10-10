# Studio history repository

## Overview

The `FileSystemStudioHistoryRepository` adapter (`lektor.adapters.storage.studio_repository`) implements `StudioHistoryRepositoryProtocol`. It provides persistent storage for Markdown TTS Studio recordings, verifying metadata against existing audio files on disk.

---

## 1. Storage structure

- **Metadata Index**: `data/audio_book/studio/history.json`
- **Audio Files**: `data/audio_book/studio/<id>.wav`

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

## 2. Physical disk synchronization

* `get_history()`: Reads entries from `history.json` and verifies that the corresponding `.wav` file exists on disk. Sets `audio_exists` accordingly.
* `add_or_update_item(item)`: Prepends newly generated recordings to the top of the history list and persists JSON to disk.
* `delete_item(item_id)`: Removes the entry from `history.json` and unlinks the associated audio file (`<id>.wav`) from disk.
