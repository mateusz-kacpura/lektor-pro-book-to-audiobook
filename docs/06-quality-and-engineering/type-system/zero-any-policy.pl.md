# Polityka braku typu Any (Zero-Any Policy)

## Przegląd

Polityka braku typu Any (ang. *Zero-Any policy*) zakłada bezwzględny zakaz stosowania dynamicznego typu `typing.Any` w kodzie produkcyjnym (`lektor/`) oraz w zestawach testowych (`tests/`). Reguła ta gwarantuje jednoznaczność kontraktów i eliminuje zjawisko utraty informacji o typach (ang. *type erasure*).

---

## 1. Mechanizm egzekwowania reguły

Zasada jest egzekwowana przez trzy uzupełniające się warstwy kontroli:

1. **Konfiguracja mypy**: Włączenie opcji `warn_return_any = True` w pliku `references/mypy.ini` natychmiast zgłasza błąd w przypadku zwrócenia wyrażenia o typie `Any`.
2. **Reguły lintera**: Zestaw reguł `ruff check` wyłapuje nieotagowane parametry i brakujące adnotacje.
3. **Bramka potoku CI**: Weryfikacja w GitHub Actions blokuje scalenie zmian w przypadku niespełnienia reguł typowania.

---

## 2. Dopuszczalne alternatywy dla typu Any

| Antywzorzec | Zalecane rozwiązanie | Przykład w kodzie |
| :--- | :--- | :--- |
| `data: Any` | Typ `object` ze sprawdzaniem typu | `def parse(data: object) -> None: if isinstance(data, dict): ...` |
| `dict[str, Any]` | `dict[str, object]` lub model Pydantic | `def save_state(state: dict[str, object]) -> None:` |
| `def get() -> Any` | Typowanie strukturalne `Protocol` | `def get_engine() -> TTSEngineProtocol:` |
| `arg: Any` | Unie typów `Union[T1, T2]` lub generyki | `def identity[T](val: T) -> T:` |
| Dowolny łańcuch `str` | Silny identyfikator `NewType` | `slug: BookSlug` zamiast `slug: str` |

---

## 3. Integracja z bibliotekami bez deklaracji typów

W przypadku korzystania z bibliotek zewnętrznych pozbawionych deklaracji typów (np. `silero-vad` lub stubs `librosa`):
- Wywołanie biblioteki musi być zamknięte w dedykowanym adapterze.
- Wynik jest rzutowany za pomocą `typing.cast(TypDocelowy, wartosc)`.
- Zewnętrzny, nieotagowany obiekt nigdy nie może przeniknąć poza warstwę adaptera do przypadków użycia w warstwie aplikacji.
