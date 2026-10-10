# Reguły biznesowe: katalog i identyfikatory (BR-001 do BR-005)

## Przegląd

Niniejsze reguły biznesowe definiują niezmienniki domenowe dotyczące identyfikacji książek, struktury katalogowej oraz indeksowania stron w rdzeniu systemu Lektor Pro.

---

### BR-001: Walidacja formatu identyfikatora książki (slug)

- **Treść reguły**: Identyfikator książki (`BookSlug`) musi składać się wyłącznie z małych liter alfabetu łacińskiego, cyfr oraz znaków podkreślenia (`[a-z0-9_]`).
- **Niezmiennik**: Identyfikator nie może zawierać spacji, wielkich liter, myślników ani znaków interpunkcyjnych.
- **Egzekwowanie**: Weryfikowane przez funkcję `lektor.domain.conversion_models.validate_book_slug`. Wystąpienie niedozwolonego znaku powoduje natychmiastowe zgłoszenie wyjątku `ValueError`.
- **Normalizacja pomocnicza**: Funkcja `lektor.domain.conversion_models.to_book_slug` usuwa znaki specjalne, zamienia spacje na podkreślenia i przekształca litery na małe.

```python
# Poprawne identyfikatory
"cloud_native_go"
"clean_architecture_python"
"go_concurrency_2026"

# Niepoprawne identyfikatory (zgłaszają ValueError)
"Cloud-Native-Go"   # Myślniki i wielkie litery są zabronione
"go concurrency"    # Spacje są zabronione
"book$name"         # Symbole specjalne są zabronione

```

---

### BR-002: Pojedyncze źródło prawdy w strukturze katalogów (SSOT)

* **Treść reguły**: Każda encja książki musi posiadać wyodrębniony katalog w magazynie danych o ścieżce: `data/books/<slug>/`.
* **Niezmiennik**: Struktura podkatalogów książki jest ściśle określona i musi zawierać:
* `pages/`: Wygenerowane pliki Markdown w języku polskim (`page_001.md`).
* `scans/`: Wyrenderowane rastrowe obrazy JPEG w 300 DPI (`page_001.jpg`).
* `audio/`: Pliki dźwiękowe mowy (`page_001.wav`), pliki podglądu (`page_001_normalized.txt`) oraz pliki stanu syntezy.
* `images/`: Wyekstrahowane ilustracje i zasoby graficzne.
* `metadata.json`: Strukturalny plik metadanych książki (`BookMetadata`).


* **Egzekwowanie**: Zdefiniowane w obiekcie wartości `lektor.domain.book_models.BookPaths`.

---

### BR-003: Ściśle dodatnia numeracja stron

* **Treść reguły**: Numeracja stron we wszystkich dokumentach, skanach i nagraniach audio musi być reprezentowana przez liczby całkowite dodatnie ($N \ge 1$).
* **Niezmiennik**: Numery stron mniejsze od jedynki ($0$ lub liczby ujemne) są odrzucane jako niepoprawne.
* **Egzekwowanie**: Wymuszane przez funkcję `lektor.domain.book_models.create_page_number`, zwracającą silny typ `PageNumber`.

```python
# Ograniczenie domenowe
def create_page_number(value: int) -> PageNumber:
    if value < 1:
        raise ValueError(f"Numer strony musi być >= 1, otrzymano: {value}")
    return PageNumber(value)

```

---

### BR-004: Standard nazewnictwa plików stron

* **Treść reguły**: Pliki powiązane ze stronami (skany, Markdown, nagrania audio) muszą posiadać jednolity prefiks oraz trzycyfrowy numer dopełniony zerami.
* **Niezmiennik**: Nazwa pliku tworzona jest według formuły:

$$\text{nazwa} = \text{prefiks} + \text{str}(N).\text{zfill}(3) + \text{rozszerzenie}$$


* **Przykłady**:
* Skan strony: `page_042.jpg`
* Dokument Markdown: `page_042.md`
* Ścieżka dźwiękowa: `page_042.wav`
* Podgląd tekstu: `page_042_normalized.txt`


* **Egzekwowanie**: Realizowane przez funkcję `lektor.domain.conversion_models.format_page_filename`.

---

### BR-005: Wyłączność aktywnego kontekstu książki

* **Treść reguły**: W danym momencie w kontenerze aplikacji aktywna może być dokładnie jedna książka.
* **Niezmiennik**: Wybór aktywnej książki determinuje powiązania ścieżek w obiekcie `DataPaths`. Po zmianie książki instancje repozytoriów stron i plików muszą zostać unieważnione metodą `reset_book_context`.
* **Egzekwowanie**: Wdrożone w przypadku użycia `lektor.application.use_cases.switch_active_book.SwitchActiveBookUseCase` i zapisywane w pliku `data/books/.active`.
