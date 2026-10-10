# ADR-004: Wybór natywnych modułów ECMAScript bez zewnętrznych frameworków SPA

## Kontekst
Współczesne aplikacje internetowe powszechnie wykorzystują frameworki oparte na ekosystemie Node.js (React, Next.js). W przypadku lokalnej aplikacji wspomaganej sztuczną inteligencją, konieczność utrzymywania środowiska Node.js, procesów budowania oraz narzut hydracji frameworków opóźniają pierwsze renderowanie widoku i komplikują dystrybucję kodu.

## Decyzja
Zaimplementowano interfejs użytkownika w oparciu o czysty standard ECMAScript Modules (ESM) bez etapu kompilacji i bundlerów:
- Logika podzielona jest na moduły JavaScript (`app.js`, `player.js`, `desktop.js`, `notes.js`, `ui.js`, `api.js`) serwowane bezpośrednio przez serwer FastAPI.
- Stan aplikacji jest synchronizowany za pomocą zdarzeń przeglądarki, zapytań HTTP i strumieni zdarzeń SSE (`EventSource`).
- Parsowanie dokumentów Markdown odbywa się po stronie przeglądarki za pomocą biblioteki `marked.min.js`.
- Przesuwanie i zmiana rozmiaru okien pulpitu bazuje na natywnym interfejsie Pointer Events w `desktop.js`.

## Lokalizacja interfejsu

Warstwa GUI posiada wspólny mechanizm lokalizacji po stronie przeglądarki:

- `static/js/i18n.js` ładuje katalog `pl.json` lub `en.json`, nakłada klucze na DOM i emituje zdarzenie `lektor:locale-changed`;
- `static/i18n/pl.json` i `static/i18n/en.json` są równoległymi katalogami o identycznym zestawie kluczy;
- `templates/partials/locale_switcher.html` jest współdzielony przez `index.html` i `studio.html`;
- lista `🇵🇱 PL` / `🇬🇧 EN` znajduje się po prawej stronie górnej nawigacji i korzysta z `localStorage` (`lektor_ui_locale`);
- `layout.css` zapewnia spójny wygląd listy z przyciskami nawigacji bez wprowadzania frameworka frontendowego.

Zmiana języka GUI nie zmienia języka wejściowego syntezy mowy ani języka tłumaczenia dokumentu. Są to niezależne ustawienia domenowe.
## Konsekwencje
- **Pozytywne:**
  - Brak etapu budowania: zmiany w plikach HTML, CSS i JS są widoczne natychmiast po odświeżeniu strony.
  - Błyskawiczny czas ładowania (First Contentful Paint) i minimalne zużycie pamięci operacyjnej przeglądarki.
  - Brak konieczności instalowania środowiska Node.js w środowisku Python.
- **Negatywne:**
  - Zarządzanie stanem i obsługa powiązań DOM wymagają dyscypliny w kodzie modułów. w kodzie modułów.
