# Graphical interface localization

## Purpose

Lektor Pro provides two GUI presentation languages:

- `pl` — Polish, the default locale,
- `en` — English.

Interface localization covers labels, titles, messages, hints, and control descriptions only. It does not change the language of text sent to speech synthesis or the target language used for page translation. Those settings are handled independently by the relevant application modules.

## Directory organization

| Element | Responsibility |
|---|---|
| `lektor/adapters/gui/static/js/i18n.js` | Catalog loading, locale selection, interpolation, and DOM translation. |
| `lektor/adapters/gui/static/i18n/pl.json` | Polish catalog. |
| `lektor/adapters/gui/static/i18n/en.json` | English catalog. |
| `lektor/adapters/gui/templates/partials/locale_switcher.html` | Shared language selector used by the audiobook and studio views. |
| `lektor/adapters/gui/static/css/layout.css` | Styling for the right side of the top navigation and the dropdown. |
| `tests/unit/test_gui_i18n.py` | Translation key and integration-contract checks. |

The shared template fragment prevents separate selector implementations in `index.html` and `studio.html`.

## User-visible behavior

1. On startup, the application reads the stored locale from `localStorage` under `lektor_ui_locale`.
2. If no valid value is stored, Polish is selected.
3. The dropdown is placed on the right side of the top navigation next to the `Audiobook` / `TTS Studio` switcher.
4. The dropdown exposes exactly two options: `🇵🇱 PL` and `🇬🇧 EN`.
5. Changing the selection loads the catalog and applies translations without a page reload.
6. The change emits `lektor:locale-changed`, allowing modules that render dynamic content to refresh their messages.

## Translation keys in HTML

Static elements use `data-*` attributes:

```html
<span data-i18n="nav.studio">TTS Studio</span>
<input data-i18n-placeholder="notes.placeholder">
<button data-i18n-title="common.close">Close</button>
```

Supported attributes are:

- `data-i18n` — element text,
- `data-i18n-html` — controlled HTML fragment,
- `data-i18n-placeholder` — field placeholder,
- `data-i18n-title` — control tooltip,
- `data-i18n-aria-label` — assistive-technology label.

Keys are hierarchical, for example `language.label` and `studio.generate`. Both JSON catalogs must contain the same set of non-empty keys.

## Dynamic content

JavaScript modules use the shared `t(key, params)` function. Parameters are interpolated with `{{name}}`, for example `t("audiobook.progress", { ready, total })`. This keeps generated messages centralized instead of duplicating strings across views.

## Testing

Localization checks can be run with:

```powershell
python -m pytest -q tests/unit/test_gui_i18n.py
python -m ruff check tests/unit/test_gui_i18n.py
python -m mypy --config-file references/mypy.ini tests/unit/test_gui_i18n.py
```

The tests verify catalog parity, duplicate-key rejection, coverage of template and JavaScript keys, and the shared selector contract in both main views.