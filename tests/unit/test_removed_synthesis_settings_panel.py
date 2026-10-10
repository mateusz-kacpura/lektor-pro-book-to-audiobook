from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
INDEX_TEMPLATE: Final[Path] = PROJECT_ROOT / "lektor" / "adapters" / "gui" / "templates" / "index.html"
DESKTOP_SCRIPT: Final[Path] = PROJECT_ROOT / "lektor" / "adapters" / "gui" / "static" / "js" / "desktop.js"
BATCH_CONTROLLER: Final[Path] = (
    PROJECT_ROOT / "lektor" / "adapters" / "gui" / "static" / "js" / "modules" / "batch_controller.js"
)


REMOVED_PANEL_MARKERS: Final[tuple[str, ...]] = (
    'id="win-settings"',
    'id="tabSettingsBtn"',
    'id="btnRegeneratePage"',
    'id="sliderTemp"',
    'id="sliderCfg"',
    'id="sliderExag"',
    'id="settingVoice"',
    'id="langSelectorGroup"',
)


def test_index_template_does_not_render_removed_synthesis_settings_panel() -> None:
    template = INDEX_TEMPLATE.read_text(encoding="utf-8")

    for marker in REMOVED_PANEL_MARKERS:
        assert marker not in template
    assert 'data-target="win-settings"' not in template


def test_desktop_layout_does_not_reference_removed_settings_window() -> None:
    desktop_script = DESKTOP_SCRIPT.read_text(encoding="utf-8")

    assert "win-settings" not in desktop_script
    assert "settingsTab" not in desktop_script


def test_batch_controller_uses_shared_defaults_without_panel_dom_dependencies() -> None:
    controller = BATCH_CONTROLLER.read_text(encoding="utf-8")

    assert "const DEFAULT_SYNTHESIS_PARAMS" in controller
    assert "...DEFAULT_SYNTHESIS_PARAMS" in controller
    for marker in REMOVED_PANEL_MARKERS[2:]:
        assert marker not in controller
