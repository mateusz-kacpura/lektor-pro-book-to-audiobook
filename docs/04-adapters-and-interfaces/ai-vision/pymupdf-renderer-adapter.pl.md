# Adapter renderera PDF PyMuPDF

## Przegląd

Adapter `PyMuPdfSplitterAdapter` (`lektor.adapters.ocr.pdf_splitter`) dostarcza implementację portu `PdfSplitterProtocol`. Wykorzystując bibliotekę PyMuPDF (`fitz`), przekształca wektorowe strony dokumentów PDF w rastrowe obrazy JPEG o wysokiej rozdzielczości, niezbędne do bezbłędnej analizy przez modele wizyjne.

---

## 1. Skalowanie rozdzielczości i transformacja macierzy

Zgodnie z regułą biznesową `BR-011`, strony są renderowane w rozdzielczości 300 DPI w celu zachowania czytelności kodu źródłowego, znaków diakrytycznych i etykiet na diagramach.

```mermaid
flowchart LR
    PDF[Wektorowa strona PDF] --> Matrix[Transformacja macierzy PyMuPDF 300/72]
    Matrix --> Pixmap[Generowanie rastra RGB Pixmap]
    Pixmap --> Save[Zapis JPEG - obraz 300 DPI]
    Save --> Scan[Domenowa encja DocumentScan]

```

### Formuła przeliczania rozdzielczości

Domyślna przestrzeń wektorowa dokumentów PDF definiowana jest w oparciu o $72\text{ punkty na cal}$. Skala powiększenia macierzy wynosi:

$$\text{skala} = \frac{\text{dpi}}{72{,}0} = \frac{300}{72{,}0} \approx 4{,}166667$$

```python
matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
pixmap = page.get_pixmap(matrix=matrix, alpha=False)
pixmap.save(str(destination_path))

```

---

## 2. Implementacja metod portu

Klasa realizuje wszystkie wymagania protokołu `PdfSplitterProtocol`:

* `split_pdf(pdf_path, output_dir, dpi=300, start_page=None, end_page=None)`: Przechodzi przez strony dokumentu, renderuje wskazany zakres i zwraca listę encji `DocumentScan`.
* `get_page_count(pdf_path)`: Otwiera nagłówek dokumentu i zwraca łączną liczbę stron (`len(doc)`) bez pełnego ładowania danych do pamięci.
* `render_page(pdf_path, page_index_0based, output_path, dpi=300)`: Renderuje pojedynczą stronę o wskazanym indeksie, wykorzystywana przez asynchroniczny potok strumieniowania skanów (`RenderPdfScansStreamUseCase`).
