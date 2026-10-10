# Memory leak profiling protocol

## Overview

The `ResourceProfiler` utility (`tests.benchmark.profiler`) implements rigorous memory leak detection and profiling. It pairs standard Python `tracemalloc` snapshots with explicit garbage collection boundaries to isolate uncollected references.

---

## 1. Profiling workflow

```mermaid
sequenceDiagram
    autonumber
    participant Runner as Benchmark Suite
    participant Profiler as ResourceProfiler
    participant Target as Function Under Test
    participant GC as Python Garbage Collector
    participant Trace as tracemalloc API

    Runner->>Profiler: run(target_fn, iterations=30, warmup=3)
    activate Profiler
    loop Warmup iterations
        Profiler->>Target: execute()
    end
    Profiler->>GC: gc.collect()
    Profiler->>Trace: start() & clear_traces()
    Profiler->>Trace: take_snapshot() [initial]

    loop Test iterations
        Profiler->>Target: execute()
    end

    Profiler->>GC: gc.collect() [isolate leaks]
    Profiler->>Trace: take_snapshot() [final]
    Profiler->>Trace: compare_to(initial, 'lineno')

    Profiler->>Profiler: Evaluate cumulative growth
    alt Cumulative growth > max_allowed_leak_growth_bytes
        Profiler-->>Runner: BenchmarkResult(leak_detected=True)
    else Clean
        Profiler-->>Runner: BenchmarkResult(leak_detected=False)
    end
    deactivate Profiler

```

---

## 2. Memory leak determination criteria

A test run is flagged with `leak_detected = True` if and only if:

$$\sum_{\text{stat} \in \text{diff}} \max(0, \text{stat.size\_diff}) > \text{max\_allowed\_leak\_growth\_bytes}$$

* **Warmup elimination**: Prevents initial one-time module imports and lookup table allocations from registering as false leaks.
* **Post-run garbage collection**: Guarantees that circular references collectible by `gc.collect()` do not trigger false alarms.
* **Top allocations reporting**: Captured snapshots log the top three code lines responsible for heap allocations to simplify remediation.
