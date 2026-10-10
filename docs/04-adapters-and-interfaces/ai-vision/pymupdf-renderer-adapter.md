# PyMuPDF renderer adapter

## Overview

The `PyMuPdfSplitterAdapter` (`lektor.adapters.ocr.pdf_splitter`) implements the `PdfSplitterProtocol` port contract. Built on the high-performance C-backed PyMuPDF library (`fitz`), it renders source PDF pages into standalone high-resolution raster JPEG bitmaps required for vision translation.

---

## 1. Resolution and matrix transformation

Following business rule `BR-011`, PDF pages are rendered at 300 DPI to preserve fine code listings, typography, and architectural diagrams.

```mermaid
flowchart LR
    PDF[Vector PDF Page] --> Matrix[PyMuPDF Matrix Transform 300/72]
    Matrix --> Pixmap[RGB Pixmap Generation]
    Pixmap --> Save[JPEG Export - 300 DPI Bitmap]
    Save --> Scan[DocumentScan Entity]

```

### Mathematical scale transformation

Since default vector PDF space is defined at $72\text{ points per inch}$, the zoom factor applied to the rendering matrix is:

$$\text{scale} = \frac{\text{dpi}}{72.0} = \frac{300}{72.0} \approx 4.166667$$

```python
matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
pixmap = page.get_pixmap(matrix=matrix, alpha=False)
pixmap.save(str(destination_path))

```

---

## 2. Adapter interface implementation

The adapter satisfies `PdfSplitterProtocol` completely:

* `split_pdf(pdf_path, output_dir, dpi=300, start_page=None, end_page=None)`: Iterates through the document, renders target slices, and returns a list of `DocumentScan` entities.
* `get_page_count(pdf_path)`: Opens document metadata and queries `len(doc)` in zero-allocation mode.
* `render_page(pdf_path, page_index_0based, output_path, dpi=300)`: Renders an isolated single page on demand, used by background streaming endpoints (`RenderPdfScansStreamUseCase`).
