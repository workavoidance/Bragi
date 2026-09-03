from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALPHA_ROOT = ROOT / "website" / "alpha"
ALPHA_PAGE = ALPHA_ROOT / "index.html"
ALPHA_SCRIPT = ALPHA_ROOT / "alpha.js"
MAIN_SCRIPT = ROOT / "website" / "script.js"


def test_alpha_page_has_current_install_feedback_and_school_paths() -> None:
    page = ALPHA_PAGE.read_text(encoding="utf-8")

    assert "Skrivi-v0.2.0-alpha.2-windows-x64-setup.exe" in page
    assert 'href="../feedback/"' in page
    assert 'href="../#schools"' in page
    assert "SCHOOL_EXPLAINER_NB.md" in page
    assert "SCHOOL_EXPLAINER.md" in page


def test_alpha_page_is_explicit_about_early_release_and_privacy() -> None:
    page = ALPHA_PAGE.read_text(encoding="utf-8")

    assert "SmartScreen" in page
    assert "ikke kodesignert ennå" in page
    assert "not code-signed yet" in page
    assert "Ikke legg ut private elevopplysninger" in page
    assert "Do not post private student information" in page


def test_alpha_page_explains_language_and_model_experiments() -> None:
    page = ALPHA_PAGE.read_text(encoding="utf-8")

    assert "Automatisk" in page
    assert "Automatic" in page
    assert "Small" in page
    assert "Base" in page
    assert "Medium" in page
    assert "hvilket verktøy barnet faktisk velger" in page


def test_alpha_guide_includes_stable_visual_settings_walkthrough() -> None:
    script = ALPHA_SCRIPT.read_text(encoding="utf-8")

    assert "assets/tray-settings.webp" in script
    assert "assets/settings-window.webp" not in script
    assert "walkthrough-settings-map" in script
    assert "Finn Skrivi og åpne Innstillinger" in script
    assert "Try languages and models" in script
    assert (ALPHA_ROOT / "assets" / "tray-settings.webp").is_file()
    assert (ALPHA_ROOT / "screenshots.css").is_file()


def test_main_site_links_to_alpha_guide() -> None:
    script = MAIN_SCRIPT.read_text(encoding="utf-8")

    assert "alpha/" in script
    assert "Test Skrivi" in script
