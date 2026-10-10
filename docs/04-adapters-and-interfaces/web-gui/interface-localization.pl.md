# Lokalizacja interfejsu graficznego

## Cel

Interfejs Lektor Pro udostępnia dwa języki prezentacji GUI:

- `pl` — język polski, ustawienie domyślne,
- `en` — język angielski.

Lokalizacja interfejsu dotyczy wyłącznie napisów, etykiet, tytułów, komunikatów i opisów kontrolek. Nie zmienia języka tekstu przekazywanego do syntezy mowy ani języka tłumaczenia stron. Te ustawienia są obsługiwane niezależnie przez odpowiednie moduły aplikacji.

## Organizacja katalogów

| Element | Odpowiedzialność |
|---|---|
| `lektor/adapters/gui/static/js/i18n.js` | Wczytywanie katalogu, wybór języka, interpolacja i nakładanie tłumaczeń na DOM. |
| `lektor/adapters/gui/static/i18n/pl.json` | Katalog polski. |
| `lektor/adapters/gui/static/i18n/en.json` | Katalog angielski. |
| `lektor/adapters/gui/templates/partials/locale_switcher.html` | Wspólny selektor języka używany przez widok audiobooka i studio. |
| `lektor/adapters/gui/static/css/layout.css` | Stylowanie prawej części górnej nawigacji i listy rozwijanej. |
| `tests/unit/test_gui_i18n.py` | Kontrola kompletności kluczy i użycia mechanizmu tłumaczeń. |

Jeden wspólny fragment szablonu zapobiega powielaniu selektora w `index.html` i `studio.html`.

## Zachowanie użytkownika

1. Po uruchomieniu aplikacja odczytuje zapamiętany język z `localStorage` pod kluczem `lektor_ui_locale`.
2. Jeżeli zapis nie istnieje albo jest niepoprawny, używany jest język polski.
3. Lista rozwijana znajduje się po prawej stronie górnego menu, obok przełącznika `Audiobook` / `Studio TTS`.
4. Lista pokazuje wyłącznie dwie opcje: `🇵🇱 PL` oraz `🇬🇧 EN`.
5. Po zmianie wyboru katalog jest wczytywany, a tłumaczenia są nakładane bez przeładowywania strony.
6. Zmiana emituje zdarzenie `lektor:locale-changed`, dzięki czemu moduły generujące dynamiczne treści mogą odświeżyć swoje komunikaty.

## Klucze tłumaczeń w HTML

Elementy statyczne korzystają z atrybutów `data-*`:

```html
<span data-i18n="nav.studio">Studio TTS</span>
<input data-i18n-placeholder="notes.placeholder">
<button data-i18n-title="common.close">Zamknij</button>
```

Obsługiwane są:

- `data-i18n` — tekst elementu,
- `data-i18n-html` — kontrolowany fragment HTML,
- `data-i18n-placeholder` — tekst zastępczy pola,
- `data-i18n-title` — podpowiedź kontrolki,
- `data-i18n-aria-label` — opis dla technologii asystujących.

Klucze są hierarchiczne, np. `language.label` albo `studio.generate`. Oba katalogi JSON muszą zawierać ten sam zestaw niepustych kluczy.

## Treści dynamiczne

Kod JavaScript korzysta ze wspólnej funkcji `t(key, params)`. Parametry są podstawiane przez zapis `{{nazwa}}`, np. `t("audiobook.progress", { ready, total })`. Dzięki temu komunikaty generowane w różnych modułach nie zawierają osobnych kopii tekstu dla każdego widoku.

## Testowanie

Podstawowa kontrola lokalizacji:

```powershell
python -m pytest -q tests/unit/test_gui_i18n.py
python -m ruff check tests/unit/test_gui_i18n.py
python -m mypy --config-file references/mypy.ini tests/unit/test_gui_i18n.py
```

Testy sprawdzają kompletność katalogów, brak duplikatów kluczy, obecność wszystkich kluczy użytych w szablonach i JavaScripcie oraz wspólną obecność selektora w obu głównych widokach.