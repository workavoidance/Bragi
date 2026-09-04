from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = "v0.2.0-alpha.4"
INSTALLER = f"Skrivi-{TAG}-windows-x64-setup.exe"
PUBLIC_TAG = "v0.2.0-alpha.3"
PUBLIC_INSTALLER = f"Skrivi-{PUBLIC_TAG}-windows-x64-setup.exe"
PUBLIC_INSTALLER_URL = (
    "https://github.com/workavoidance/Skrivi/releases/download/"
    f"{PUBLIC_TAG}/{PUBLIC_INSTALLER}"
)


def test_alpha_version_is_consistent_across_package_and_installer() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package = (ROOT / "src" / "whisper_dictate" / "__init__.py").read_text(
        encoding="utf-8"
    )
    installer = (ROOT / "build_installer.ps1").read_text(encoding="utf-8")
    preview = (ROOT / ".github" / "workflows" / "preview.yml").read_text(
        encoding="utf-8"
    )

    assert project["project"]["version"] == "0.2.0a4"
    assert '__version__ = "0.2.0a4"' in package
    assert '[string]$Version = "0.2.0-alpha.4"' in installer
    assert '-Version "0.2.0-alpha.4-pr.${{ github.event.pull_request.number }}"' in (
        preview
    )


def test_website_stays_on_previous_alpha_until_store_release_is_accepted() -> None:
    website = (ROOT / "website" / "index.html").read_text(encoding="utf-8")

    assert website.count(PUBLIC_INSTALLER_URL) == 2


def test_readme_links_directly_to_current_alpha_installer() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    release_url = (
        f"https://github.com/workavoidance/Skrivi/releases/download/{TAG}/{INSTALLER}"
    )

    assert release_url in readme
    assert "install the standard 64-bit Python" not in readme.casefold()


def test_tagged_release_uses_curated_notes_and_marks_alpha_as_prerelease() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    notes = ROOT / "docs" / "releases" / f"{TAG}.md"

    assert '"--notes-file", $notesFile' in workflow
    assert '$prereleaseArgs = @("--prerelease")' in workflow
    assert '--target "${{ github.sha }}"' in workflow
    assert "gh release upload $tag @assets --clobber" in workflow
    assert '$ErrorActionPreference = "SilentlyContinue"' in workflow
    assert '".github/workflows/release.yml"' in workflow
    assert notes.is_file()
    assert "not code-signed" in notes.read_text(encoding="utf-8")


def test_release_version_file_matches_the_public_download() -> None:
    version = (ROOT / "release" / "VERSION").read_text(encoding="utf-8").strip()

    assert version == TAG
