# ADR-003: Single Source of Truth filesystem storage

## Context
Audiobook generation produces heterogeneous digital assets for each book: raw PDF files, high-resolution rendering scans (300 DPI JPG), extracted and translated Markdown files, normalized phonetics files (`_normalized.txt`), WAV audio chunks, and telemetry state tracking files. Using an external relational database would introduce external service dependencies and complicate local data portability.

## Decision
We designate the directory tree under `data/books/<slug>/` as the authoritative Single Source of Truth (SSOT):
- Each book resides in a strictly isolated directory named after its sanitized `BookSlug`.
- Standardized directory layout:
  - `original/` or root: original binary document (`.pdf`).
  - `scans/`: rendered sequential JPG files (`page_%03d.jpg`).
  - `pages/`: extracted Markdown files (`page_%03d.md`) with JSON metadata headers and scan footers.
  - `audio/`: generated WAV files, normalized text files, and state manifests.
  - `metadata.json`: authoritative book metadata (title, author, total pages, language).
- The `FileSystemBookRepository` coordinates all mutations, ensuring directories exist before file operations.

## Consequences
- **Positive:**
  - Complete data portability: a book can be backed up or inspected using standard OS file tools.
  - Zero external database management overhead.
- **Negative:**
  - High concurrency updates must rely on filesystem locks and atomic write patterns.ng.
