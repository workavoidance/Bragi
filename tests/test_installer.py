from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_installer_is_per_user_and_does_not_request_administrator_rights() -> None:
    script = (ROOT / "installer" / "Skrivi.iss").read_text(encoding="utf-8")

    assert "DefaultDirName={localappdata}\\Programs\\Skrivi" in script
    assert "PrivilegesRequired=lowest" in script
    assert "MinVersion=10.0.22000" in script
    assert "UninstallDisplayIcon={app}\\Skrivi.exe" in script


def test_installer_manages_program_files_but_never_user_data() -> None:
    script = (ROOT / "installer" / "Skrivi.iss").read_text(encoding="utf-8")

    assert "{app}\\runtime" in script
    assert "{appdata}" not in script.casefold()
    assert "models" not in script.casefold()
    assert "[UninstallDelete]" not in script


def test_uninstaller_removes_only_its_own_automatic_startup_entry() -> None:
    script = (ROOT / "installer" / "Skrivi.iss").read_text(encoding="utf-8")

    assert "CompareText(RegisteredCommand, InstalledCommand) = 0" in script
    assert "RegDeleteValue" in script
    assert "uninsdeletevalue" not in script.casefold()


def test_installed_build_uses_one_folder_packaging() -> None:
    script = (ROOT / "build_installer.ps1").read_text(encoding="utf-8")

    assert "--onedir" in script
    assert "--contents-directory runtime" in script
    assert "BUILD_INFO.json" in script


def test_preview_and_release_workflows_build_the_installer() -> None:
    preview = (ROOT / ".github" / "workflows" / "preview.yml").read_text(
        encoding="utf-8"
    )
    release = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )

    assert "build_installer.ps1" in preview
    assert "windows-x64-setup.exe" in preview
    assert "build_installer.ps1" in release
    assert "windows-x64-setup.exe.sha256" in release
