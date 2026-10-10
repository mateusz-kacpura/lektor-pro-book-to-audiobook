# Weryfikacja typów za pomocą mypy

## Przegląd

Projekt Lektor Pro wymusza statyczną kontrolę typów za pomocą narzędzia `mypy`. Zastosowana konfiguracja zapobiega błędom w czasie wykonywania programu, gwarantuje zgodność z protokołami oraz eliminuje niejawne typowanie dynamiczne w kodzie źródłowym i testach.

---

## 1. Konfiguracja narzędzia mypy (`references/mypy.ini`)

Plik konfiguracyjny projektu definiuje rygorystyczne reguły sprawdzania:

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

## 2. Automatyczna weryfikacja w potoku CI

Statyczna analiza typów jest uruchamiana lokalnie oraz jako obowiązkowy krok w potoku ciągłej integracji:

```powershell
python -m mypy --config-file references/mypy.ini lektor tests

```

### Wynik weryfikacji

```text
Success: no issues found in 131 source files

```

---

## 3. Kluczowe reguły konfiguracyjne

1. **`warn_return_any = True`**: Zakazuje zwracania nieotagowanych typów z funkcji posiadających jawne sygnatury wyjściowe.
2. **`disallow_untyped_defs = True`**: Wymusza deklarację typów argumentów i zwracanych wartości dla wszystkich funkcji w projekcie i testach.
3. **`strict_optional = True`**: Wymaga jawnej obsługi wartości `None` dla typów opcjonalnych `Optional[T]` przed wywołaniem ich metod.
