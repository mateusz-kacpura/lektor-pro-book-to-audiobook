# Live task state persistence specification

## Overview

This specification details the disk-based persistence model used to record, synchronize, and recover execution state for in-progress speech synthesis and document conversions. Stored primarily in `.generator_state.json` inside the book audio directory, this mechanism prevents telemetry desynchronization between long-running worker threads and browser pollers.

---

## 1. File placement & atomic writes

- **Path**: Located at `data/books/<slug>/audio/.generator_state.json`.
- **Concurrency control**: Handled via `threading.RLock` within `JobExecutionManager` and atomic file write patterns (writing to a temporary file before renaming) to avoid partial-read JSON decoding errors in concurrent readers.
- **Cleanup invariant**: The file is removed immediately when a batch completes, aborts, or halts cleanly.

---

## 2. JSON schema specification

The persisted payload contains the following keys:

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

### Field semantics

* `page_id`: Stem of the active page document without extension.
* `current_idx` / `total_pages`: Absolute page counter across the entire book catalog.
* `percentage`: Overall conversion progress ($0.0 \le P \le 100.0$).
* `timestamp`: POSIX epoch timestamp (`time.time()`) of the most recent worker heartbeat.
* `current_segment` / `total_segments`: Granular utterance progress within the current page.
* `current_sentence`: Quoted string of the exact normalized sentence currently processed by the neural vocoder.

---

## 3. Freshness & stale state invalidation

Managed by `parse_active_task_stage` in `lektor.adapters.gui.state`:

$$\text{is\_valid} = (\text{now}() - \text{timestamp}) < 180.0\text{ seconds}$$

If the system crashes or experiences an ungraceful shutdown, stale state files are ignored after three minutes ($180\text{ s}$), preventing UI components from displaying permanent mock progress.
