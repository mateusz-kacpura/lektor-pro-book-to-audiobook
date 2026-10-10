# File system page repository

## Overview

The `FileSystemPageRepository` adapter (`lektor.adapters.storage.file_repository`) satisfies `PageRepositoryProtocol`. It manages page file reading, atomic writing, normalized preview storage, and progress state files.

---

## 1. Key operations and invariants

### Markdown document I/O
- `read_markdown(path)`: Reads text strictly using UTF-8 encoding with replacement fallback for invalid byte sequences.
- `write_markdown(path, content)`: Ensures parent directories exist (`mkdir(parents=True)`) and writes content atomically.

### Discovery and natural sorting
- `list_pages(directory, pattern="*.md")`: Scans directory and numerically sorts page files so `page_9.md` precedes `page_10.md`:

```python
def _extract_number(path: Path) -> int:
    match = re.search(r"(\d+)", path.stem)
    return int(match.group(1)) if match else 0

```

### Media and state inspection

* `audio_exists(path, min_bytes=1000)`: Confirms an audio file exists and exceeds byte threshold, verifying header validity.
* `save_preview(path, text)`: Writes normalized speech text to `page_XXX_normalized.txt`.
* `save_state(path, state_dict)`: Serializes synthesis progress and duration metrics to JSON.
