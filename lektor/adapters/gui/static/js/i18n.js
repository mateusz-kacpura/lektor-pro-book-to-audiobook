const SUPPORTED_LOCALES = ["pl", "en"];
const DEFAULT_LOCALE = "pl";
const STORAGE_KEY = "lektor_ui_locale";
const CATALOG_VERSION = "20261009-i18n";

let currentLocale = DEFAULT_LOCALE;
let catalog = {};
let fallbackCatalog = {};

function readValue(source, key) {
  return key.split(".").reduce((value, part) => value?.[part], source);
}

function interpolate(value, params = {}) {
  return value.replace(/\{\{\s*([\w.-]+)\s*\}\}/g, (_, key) => {
    const replacement = params[key];
    return replacement === undefined || replacement === null ? `{{${key}}}` : String(replacement);
  });
}

function readStoredLocale() {
  try {
    return localStorage.getItem(STORAGE_KEY) || DEFAULT_LOCALE;
  } catch (error) {
    console.warn("Nie udało się odczytać zapisanego języka interfejsu:", error);
    return DEFAULT_LOCALE;
  }
}

function persistLocale(locale) {
  try {
    localStorage.setItem(STORAGE_KEY, locale);
  } catch (error) {
    console.warn("Nie udało się zapisać języka interfejsu:", error);
  }
}
function updateDocumentLanguage() {
  document.documentElement.lang = currentLocale;
  const selector = document.getElementById("localeSelector");
  if (selector && selector.value !== currentLocale) selector.value = currentLocale;
}

export function t(key, params = {}) {
  const value = readValue(catalog, key) ?? readValue(fallbackCatalog, key);
  if (typeof value !== "string") return key;
  return interpolate(value, params);
}

export function applyTranslations(root = document) {
  const elements = [];
  if (root instanceof Element && root.matches("[data-i18n], [data-i18n-html], [data-i18n-placeholder], [data-i18n-title], [data-i18n-aria-label]")) {
    elements.push(root);
  }
  elements.push(...root.querySelectorAll("[data-i18n], [data-i18n-html], [data-i18n-placeholder], [data-i18n-title], [data-i18n-aria-label]"));

  for (const element of elements) {
    const textKey = element.dataset.i18n;
    const htmlKey = element.dataset.i18nHtml;
    const placeholderKey = element.dataset.i18nPlaceholder;
    const titleKey = element.dataset.i18nTitle;
    const ariaLabelKey = element.dataset.i18nAriaLabel;

    if (textKey) element.textContent = t(textKey);
    if (htmlKey) element.innerHTML = t(htmlKey);
    if (placeholderKey) element.setAttribute("placeholder", t(placeholderKey));
    if (titleKey) element.setAttribute("title", t(titleKey));
    if (ariaLabelKey) element.setAttribute("aria-label", t(ariaLabelKey));
  }
}

function bindLocaleSelector() {
  const selector = document.getElementById("localeSelector");
  if (!selector || selector.dataset.i18nBound === "true") return;

  selector.dataset.i18nBound = "true";
  selector.addEventListener("change", () => {
    void setLocale(selector.value);
  });
}

async function loadCatalog(locale) {
  const response = await fetch(`/static/i18n/${locale}.json?v=${CATALOG_VERSION}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Nie udało się wczytać katalogu języka: ${locale}`);
  return response.json();
}

export async function setLocale(locale) {
  const nextLocale = SUPPORTED_LOCALES.includes(locale) ? locale : DEFAULT_LOCALE;

  try {
    catalog = await loadCatalog(nextLocale);
    currentLocale = nextLocale;
  } catch (error) {
    console.error("Nie udało się wczytać tłumaczenia interfejsu:", error);
    if (nextLocale !== DEFAULT_LOCALE) {
      try {
        catalog = await loadCatalog(DEFAULT_LOCALE);
        currentLocale = DEFAULT_LOCALE;
      } catch (fallbackError) {
        console.error("Nie udało się wczytać domyślnego tłumaczenia interfejsu:", fallbackError);
      }
    }
  }

  persistLocale(currentLocale);
  updateDocumentLanguage();
  applyTranslations(document);
  bindLocaleSelector();
  document.dispatchEvent(new CustomEvent("lektor:locale-changed", {
    detail: { locale: currentLocale },
  }));
  return currentLocale;
}

export function getLocale() {
  return currentLocale;
}

async function initI18n() {
  try {
    fallbackCatalog = await loadCatalog(DEFAULT_LOCALE);
  } catch (error) {
    console.error("Nie udało się wczytać katalogu domyślnego interfejsu:", error);
  }

  const storedLocale = readStoredLocale();
  await setLocale(storedLocale);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    applyTranslations(document);
    bindLocaleSelector();
  }, { once: true });
}
export const ready = initI18n();

window.lektorI18n = {
  ready,
  t,
  setLocale,
  getLocale,
  applyTranslations,
};
