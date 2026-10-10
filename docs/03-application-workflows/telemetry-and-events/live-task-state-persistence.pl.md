# Specyfikacja zapisu stanu zadań w toku

## Przegląd

Dokument określa mechanizm zapisu stanu aktywnych zadań syntezy mowy i konwersji na dysku. Wykorzystywany głównie poprzez plik `.generator_state.json` w katalogu audio książki, mechanizm ten umożliwia synchronizację postępu pomiędzy wątkami roboczymi a odpytywaniem z poziomu przeglądarki.

---

## 1. Lokalizacja pliku i atomowy zapis

- **Ścieżka**: Plik znajduje się pod adresem `data/books/<slug>/audio/.generator_state.json`.
- **Kontrola współbieżności**: Nadzorowana przez `threading.RLock` w klasie `JobExecutionManager`. Zapis realizowany jest z zachowaniem atomowości, aby zapobiec odczytowi niekompletnego formatu JSON przez klientów.
- **Czyszczenie po zakończeniu**: Plik jest automatycznie usuwany z dysku po poprawnym zakończeniu zadania wsadowego lub jego zatrzymaniu przez użytkownika.

---

## 2. Schemat danych formatu JSON

Zapisywany obiekt zawiera następujące pola:

```json
{
  "page_id": "page_042",
  "filename": "page_042.md",
  "current_idx": 42,
  "total_pages": 120,
  "percentage": 35.0,
  "timestamp": 1791542400.12,
  "status": "generating",
  "current_segment": 4,
  "total_segments": 18,
  "completed_segments": 3,
  "segment_percent": 22.2,
  "current_sentence": "Instrukcja wyboru select multipleksuje kanały.",
  "stage_description": "Synteza mowy: segment 4 z 18 (22.2%)"
}

```

### Znaczenie pól

* `page_id`: Identyfikator przetwarzanej strony bez rozszerzenia.
* `current_idx` / `total_pages`: Bezwzględny licznik stron w obrębie całej książki.
* `percentage`: Całościowy postęp przetwarzania ($0{,}0 \le P \le 100{,}0$).
* `timestamp`: Znacznik czasu uniksowego (`time.time()`) ostatniej aktywności wątku roboczego.
* `current_segment` / `total_segments`: Szczegółowy licznik wypowiedzi w obrębie bieżącej strony.
* `current_sentence`: Tekst znormalizowanego zdania aktualnie przetwarzanego przez model lektora.

---

## 3. Ważność i unieważnianie przedawnionego stanu

Weryfikowane przez funkcję `parse_active_task_stage` w module `lektor.adapters.gui.state`:

$$\text{czy\_poprawny} = (\text{czas\_aktualny}() - \text{timestamp}) < 180{,}0\text{ sekund}$$

W przypadku nagłego wyłączenia zasilania lub awarii procesu plik stanu starszy niż 3 minuty ($180\text{ s}$) jest uznawany za przedawniony i ignorowany, co zapobiega wyświetlaniu pozornego generowania w interfejsie.
