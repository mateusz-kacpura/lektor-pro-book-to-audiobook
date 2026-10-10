# Business rules: catalog & slugs (BR-001 to BR-005)

## Overview

These business rules define the domain invariants for book identification, catalog organization, and page indexing within the Lektor Pro core domain.

---

### BR-001: Book slug format validation

- **Statement**: A book identifier (`BookSlug`) must consist exclusively of lowercase alphanumeric characters and underscores (`[a-z0-9_]`).
- **Invariant**: The slug cannot contain spaces, uppercase letters, hyphens, or special punctuation.
- **Enforcement**: Handled by `lektor.domain.conversion_models.validate_book_slug`. If an invalid character is encountered, a `ValueError` is raised immediately.
- **Sanitization Helper**: `lektor.domain.conversion_models.to_book_slug` strips non-alphanumeric characters, converts whitespace to underscores, and lowercases text to guarantee conformance.

```python
# Valid slug examples
"cloud_native_go"
"clean_architecture_python"
"go_concurrency_2026"

# Invalid slug examples (raises ValueError)
"Cloud-Native-Go"   # Hyphens and uppercase letters forbidden
"go concurrency"    # Spaces forbidden
"book$name"         # Symbols forbidden

```

---

### BR-002: Single source of truth (SSOT) directory layout

* **Statement**: Every book entity must reside in a dedicated directory under the storage root: `data/books/<slug>/`.
* **Invariant**: The book workspace layout is strictly canonical and must contain the following subdirectories:
* `pages/`: Generated Polish Markdown files (`page_001.md`).
* `scans/`: High-resolution source JPEG bitmap renders (`page_001.jpg`).
* `audio/`: Synthesized speech tracks (`page_001.wav`), preview files (`page_001_normalized.txt`), and task state files.
* `images/`: Ancillary extracted diagram images and visual assets.
* `metadata.json`: Structured book metadata file (`BookMetadata`).


* **Enforcement**: Defined in the domain value object `lektor.domain.book_models.BookPaths`.

---

### BR-003: Strictly positive page numbering

* **Statement**: Page numbering across documents, scans, and synthesized audio must strictly be represented as positive 1-based integers ($N \ge 1$).
* **Invariant**: Page numbers less than $1$ ($0$ or negative integers) are mathematically invalid and rejected.
* **Enforcement**: Guarded by `lektor.domain.book_models.create_page_number`, which encapsulates values in the strong type `PageNumber`.

```python
# Domain constraint
def create_page_number(value: int) -> PageNumber:
    if value < 1:
        raise ValueError(f"Page number must be >= 1, received: {value}")
    return PageNumber(value)

```

---

### BR-004: Standardized page file naming pattern

* **Statement**: Stored page assets (scans, Markdown documents, and audio tracks) must share a unified prefix and a 3-digit zero-padded number.
* **Invariant**: File naming follows the format:

$$\text{filename} = \text{prefix} + \text{str}(N).\text{zfill}(3) + \text{ext}$$


* **Examples**:
* Scan bitmap: `page_042.jpg`
* Markdown page: `page_042.md`
* Audio track: `page_042.wav`
* Text preview: `page_042_normalized.txt`


* **Enforcement**: Handled by `lektor.domain.conversion_models.format_page_filename`.

---

### BR-005: Active book context exclusivity

* **Statement**: Exactly one book can hold the active state at any given point in time across the application container.
* **Invariant**: The active book selection dictates the dynamic binding of paths in `DataPaths`. When the context shifts, all cached page and file repositories must be invalidated immediately via `reset_book_context`.
* **Enforcement**: Implemented in `lektor.application.use_cases.switch_active_book.SwitchActiveBookUseCase` and persisted via `data/books/.active`.
