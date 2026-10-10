# Repozytorium stron na systemie plików

## Przegląd

Adapter `FileSystemPageRepository` (`lektor.adapters.storage.file_repository`) realizuje kontrakt `PageRepositoryProtocol`. Odpowiada za operacje wejścia/wyjścia na plikach stron Markdown, zapis podglądów normalizacji oraz zarządzanie plikami stanu syntezy.

---

## 1. Kluczowe operacje i niezmienniki

### Operacje na plikach Markdown
- `read_markdown(path)`: Odczytuje treść w kodowaniu UTF-8 z bezpieczną obsługą znaków specjalnych.
- `write_markdown(path, content)`: Zapewnia obecność katalogów nadrzędnych (`mkdir(parents=True)`) i zapisuje plik w sposób atomowy.

### Wyszukiwanie i sortowanie naturalne
- `list_pages(directory, pattern="*.md")`: Wyszukuje pliki stron i sortuje je numerycznie, dzięki czemu `page_9.md` poprzedza `page_10.md`:

```python
def _extract_number(path: Path) -> int:
    match = re.search(r"(\d+)", path.stem)
    return int(match.group(1)) if match else 0

```

### Weryfikacja mediów i zapis stanu

* `audio_exists(path, min_bytes=1000)`: Potwierdza obecność pliku dźwiękowego o poprawnym, niezerowym rozmiarze.
* `save_preview(path, text)`: Zapisuje znormalizowany tekst mowy w pliku `page_XXX_normalized.txt`.
* `save_state(path, state_dict)`: Zapisuje metadane postępu i metryki czasu trwania syntezy do pliku JSON.
