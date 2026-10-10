# Static type checking with mypy

## Overview

Lektor Pro enforces a static typing policy verified with `mypy`. This configuration eliminates runtime type errors, ensures protocol compatibility, and blocks implicit dynamic typing across production and test code.

---

## 1. Mypy configuration file (`references/mypy.ini`)

The project configuration defines strict rules:

```ini
[mypy]
python_version = 3.14
ignore_missing_imports = True
strict_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_return_any = True
warn_unreachable = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = False
no_implicit_optional = True
show_error_codes = True
pretty = True

```

---

## 2. Automated type verification

Type checking is executed locally and as an automated stage in the GitHub Actions CI pipeline:

```powershell
python -m mypy --config-file references/mypy.ini lektor tests

```

### Verification result

```text
Success: no issues found in 131 source files

```

---

## 3. Strict rules summary

1. **`warn_return_any = True`**: Forbids returning untyped expressions from functions with explicit return type annotations.
2. **`disallow_untyped_defs = True`**: Mandates explicit type annotations for all function and method signatures across both production code and test suites.
3. **`strict_optional = True`**: Enforces strict handling of `Optional[T]` types, requiring explicit `None` checks before attribute access.
