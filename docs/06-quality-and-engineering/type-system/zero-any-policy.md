# Zero-Any type safety policy

## Overview

The Zero-Any policy mandates that the dynamic fallback type `typing.Any` is strictly forbidden across production modules (`lektor/`) and test suites (`tests/`). This design rule enforces explicit typing contracts and prevents type erasure.

---

## 1. Enforcement mechanics

The policy is enforced through three complementary validation layers:

1. **Static analysis configuration**: `warn_return_any = True` in `references/mypy.ini` flags any function returning an expression typed as `Any`.
2. **Linting rules**: `ruff check` rules flag untyped arguments and dynamic type annotations.
3. **CI pipeline enforcement**: Pull requests failing static type checks cannot merge to `main`.

---

## 2. Approved typing alternatives

| Anti-pattern | Approved alternative | Example |
| :--- | :--- | :--- |
| `data: Any` | `object` with narrowing | `def parse(data: object) -> None: if isinstance(data, dict): ...` |
| `dict[str, Any]` | `dict[str, object]` or Pydantic model | `def save_state(state: dict[str, object]) -> None:` |
| `def get_handler() -> Any` | `Protocol` structural typing | `def get_engine() -> TTSEngineProtocol:` |
| `arg: Any` | `Union[T1, T2]` or `TypeVar` | `def identity[T](val: T) -> T:` |
| Generic string IDs | Strong `NewType` wrappers | `slug: BookSlug` instead of `slug: str` |

---

## 3. Interfacing with third-party untyped libraries

When consuming untyped external packages (e.g. `snakers4/silero-vad` or `librosa` stubs):
- Isolate the external call within an adapter layer boundary.
- Cast values explicitly using `typing.cast(TargetType, untyped_val)`.
- Never expose the untyped return value across interface adapter boundaries into application use cases.
