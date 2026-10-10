# ADR-001: Clean Architecture adoption and strict zero-Any type safety

## Context
The Lektor Pro platform integrates diverse subcomponents: document layout parsing, multimodal vision extraction (Gemma / Qwen), text DSP normalization, neural speech synthesis (OmniVoice / Chatterbox), and file streaming. Earlier monolithic implementations intermingled framework I/O calls directly with text normalization algorithms, resulting in brittle testing harnesses, high coupling, and silent runtime type failures when passing raw dictionaries.

## Decision
1. **Clean Architecture adoption:** We mandate strict architectural separation into four concentric layers:
   - **Domain:** Pure business invariants, entities, and value objects (`lektor.domain`). Completely isolated from external packages and hardware frameworks.
   - **Application:** Use cases and orchestration protocols (`lektor.application`). Communicates inward with domain models and outward through abstract protocols (`typing.Protocol`).
   - **Interface adapters:** Concrete implementations converting domain models to boundary representations (`lektor.adapters`). Contains FastAPI routers, CLI main loop, TTS engine adapters, and storage repositories.
   - **Frameworks and drivers:** External configuration, entry points, and low-level drivers (`lektor.infrastructure`).
2. **Zero-Any type discipline:**
   - The use of `Any` is strictly prohibited across the codebase.
   - Use `typing.NewType` for distinct domain primitives (`BookSlug`, `PageNumber`, `ConversionTaskId`, `ModelSlotId`).
   - Protocol types (`typing.Protocol`) define structural interfaces instead of relying on runtime duck-typing.
   - Mypy runs in strict mode with flags: `warn_return_any = True`, `warn_unused_ignores = True`, and `disallow_untyped_defs = True`.

## Consequences
- **Positive:**
  - Complete decoupling from underlying web frameworks and machine learning toolkits.
  - Test suites can verify 100% of domain and application behaviors in-memory with fake adapters at microsecond latencies.
  - Static type checking guarantees contract conformity before runtime execution.
- **Negative:**
  - Additional boilerplate required for DTO mapping and structural protocol definitions.ng.
