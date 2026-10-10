# ADR-004: Native Vanilla JavaScript (ES modules) client architecture

## Context
Modern frontend architectures often employ Node.js-based Single Page Application frameworks (React, Next.js). In a self-contained local desktop application executing AI pipelines, compiling large JavaScript client bundles introduces hydration overhead, Node runtime dependencies, and slower initial page paints.

## Decision
We implement the frontend using standard native ECMAScript modules (ESM) without a Node.js build pipeline:
- Components are structured as modular JS files (`app.js`, `player.js`, `desktop.js`, `notes.js`, `ui.js`, `api.js`) served directly by FastAPI.
- State is synchronized natively using standard browser DOM events, `CustomEvent`, and client-side reactive polling / Server-Sent Events (`EventSource`).
- Markdown rendering is handled locally in the browser via `marked.min.js`.
- Window management and drag-and-drop features use native Pointer Events in `desktop.js`.

## Interface localization

The GUI uses one shared browser-side localization mechanism:

- `static/js/i18n.js` loads the `pl.json` or `en.json` catalog, applies keys to the DOM, and emits `lektor:locale-changed`;
- `static/i18n/pl.json` and `static/i18n/en.json` are parallel catalogs with the same key set;
- `templates/partials/locale_switcher.html` is shared by `index.html` and `studio.html`;
- the `🇵🇱 PL` / `🇬🇧 EN` dropdown is placed on the right side of the top navigation and persists through `localStorage` (`lektor_ui_locale`);
- `layout.css` gives the dropdown the same visual language as the navigation buttons without introducing a frontend framework.

GUI language is independent from the input language used by speech synthesis and the target language used for document translation. Those are separate domain settings.
## Consequences
- **Positive:**
  - Zero build step: modifications to HTML, CSS, or JS are immediately reflected upon browser refresh.
  - Sub-millisecond initial paint and near-zero memory overhead.
  - No dependency on Node.js, npm, or frontend bundlers in the Python distribution.
- **Negative:**
  - Complex state management must be engineered cleanly without framework-level reactive state primitives.
