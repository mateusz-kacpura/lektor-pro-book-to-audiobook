"""Sprawdza kompletność katalogów i odwołań do tłumaczeń GUI."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import cast

import pytest

PROJECT_ROOT = Path(__file__).parents[2]
I18N_DIR = PROJECT_ROOT / "lektor" / "adapters" / "gui" / "static" / "i18n"
TEMPLATES_DIR = PROJECT_ROOT / "lektor" / "adapters" / "gui" / "templates"
STATIC_JS_DIR = PROJECT_ROOT / "lektor" / "adapters" / "gui" / "static" / "js"


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = [key for key, _ in pairs]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise ValueError(f"Duplikaty kluczy tłumaczeń: {duplicates}")
    return dict(pairs)


def _load_catalog(locale: str) -> dict[str, object]:
    path = I18N_DIR / f"{locale}.json"
    return cast(
        dict[str, object],
        json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys),
    )


def _flatten(value: dict[str, object], prefix: str = "") -> dict[str, str]:
    result: dict[str, str] = {}
    for key, item in value.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict):
            result.update(_flatten(item, full_key))
        else:
            result[full_key] = str(item)
    return result


def test_polish_and_english_catalogs_have_the_same_nonempty_keys() -> None:
    polish = _flatten(_load_catalog("pl"))
    english = _flatten(_load_catalog("en"))

    assert set(polish) == set(english)
    assert all(isinstance(value, str) and value.strip() for value in polish.values())
    assert all(isinstance(value, str) and value.strip() for value in english.values())


def test_all_template_translation_keys_exist_in_polish_catalog() -> None:
    keys = set(_flatten(_load_catalog("pl")))
    pattern = re.compile(r'data-i18n(?:-(?:html|placeholder|title|aria-label))?="([^"]+)"')
    used: set[str] = set()

    for path in TEMPLATES_DIR.rglob("*.html"):
        used.update(pattern.findall(path.read_text(encoding="utf-8")))

    assert used <= keys, sorted(used - keys)


def test_all_static_javascript_translation_keys_exist_in_polish_catalog() -> None:
    keys = set(_flatten(_load_catalog("pl")))
    pattern = re.compile(r'\b(?:t|tr)\(\s*["\']([^"\']+)["\']')
    used: set[str] = set()

    for path in STATIC_JS_DIR.rglob("*.js"):
        used.update(pattern.findall(path.read_text(encoding="utf-8")))

    assert used <= keys, sorted(used - keys)


@pytest.mark.parametrize("template", ["index.html", "studio.html"])
def test_main_views_include_the_top_locale_selector(template: str) -> None:
    content = (TEMPLATES_DIR / template).read_text(encoding="utf-8")
    assert "locale_switcher.html" in content
    assert "global_bottom_nav.html" not in content


def test_shared_locale_selector_is_a_flag_code_dropdown() -> None:
    content = (TEMPLATES_DIR / "partials" / "locale_switcher.html").read_text(encoding="utf-8")
    assert 'class="locale-switcher"' in content
    assert 'locale-label' not in content
    assert 'id="localeSelector"' in content
    assert 'value="pl"' in content
    assert 'value="en"' in content
    assert '🇵🇱 PL' in content
    assert '🇬🇧 EN' in content


def test_i18n_switches_locale_from_the_language_dropdown() -> None:
    content = (STATIC_JS_DIR / "i18n.js").read_text(encoding="utf-8")
    assert 'selector.addEventListener("change"' in content
    assert 'setLocale(selector.value)' in content


def test_main_views_keep_app_switcher_and_locale_selector_in_right_nav_actions() -> None:
    for template in ("index.html", "studio.html"):
        content = (TEMPLATES_DIR / template).read_text(encoding="utf-8")
        nav_start = content.index('<nav class="global-nav">')
        nav_end = content.index('</nav>', nav_start)
        nav = content[nav_start:nav_end]
        assert 'class="global-nav-actions"' in nav
        assert 'class="app-switcher"' in nav
        assert 'locale_switcher.html' in nav