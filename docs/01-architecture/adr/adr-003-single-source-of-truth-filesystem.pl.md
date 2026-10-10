# ADR-003: Pojedyncze źródło prawdy oparte na strukturze systemu plików

## Kontekst
Proces generowania audiobooka tworzy różnorodne zasoby cyfrowe dla każdej pozycji: oryginalny plik PDF, wyrenderowane skany stron (300 DPI JPG), przetłumaczone pliki Markdown, znormalizowany tekst lektorski (`_normalized.txt`), pliki audio WAV oraz metadane postępu. Zastosowanie zewnętrznej relacyjnej bazy danych wymusiłoby instalację dodatkowych usług i utrudniło przenoszenie danych między środowiskami.

## Decyzja
Struktura katalogów pod ścieżką `data/books/<slug>/` stanowi pojedyncze źródło prawdy (Single Source of Truth):
- Każda książka posiada odizolowany katalog nazwany unikalnym identyfikatorem `BookSlug`.
- Standaryzowany układ podkatalogów:
  - katalog główny: plik źródłowy PDF.
  - `scans/`: sekwencyjne obrazy stron JPG (`page_%03d.jpg`).
  - `pages/`: przetłumaczony Markdown (`page_%03d.md`) zawierający metadane JSON oraz odnośnik do skanu.
  - `audio/`: wygenerowane pliki WAV, podglądy tekstu oraz pliki stanu generatora.
  - `metadata.json`: kanoniczny plik z metadanymi książki.
- Dostęp i operacje wejścia/wyjścia realizowane są wyłącznie przez `FileSystemBookRepository`.

## Konsekwencje
- **Pozytywne:**
  - Pełna przenośność danych: kopiowanie lub archiwizacja książki wymaga jedynie przeniesienia katalogu na dysku.
  - Brak zależności od zewnętrznych silników bazodanowych.
- **Negatywne:**
  - Konieczność dbania o atomowość operacji zapisu i zabezpieczenia przed współbieżnymi modyfikacjami.
