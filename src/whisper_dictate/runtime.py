from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

APP_NAME = "Skrivi"
LEGACY_APP_NAME = "Bragi"
BUILD_INFO_FILENAME = "BUILD_INFO.json"
BUILD_INFO_ERRORS = (OSError, ValueError, KeyError, TypeError)
GIT_IDENTITY_ERRORS = (OSError, subprocess.SubprocessError)


@dataclass(frozen=True)
class BuildIdentity:
    identifier: str
    development: bool

    @property
    def title(self) -> str:
        if self.development:
            return f"{APP_NAME} DEV {self.identifier}"
        return APP_NAME


def _environment(environment: Mapping[str, str] | None) -> Mapping[str, str]:
    return os.environ if environment is None else environment


def _fallback_data_root(home: Path | None = None) -> Path:
    return (home or Path.home()) / "AppData" / "Local"


def _application_data_root(root: Path) -> Path:
    path = root / APP_NAME
    legacy_path = root / LEGACY_APP_NAME
    if not path.exists() and legacy_path.exists():
        try:
            os.replace(legacy_path, path)
        except OSError:
            # Preserving existing settings and large model downloads is safer
            # than silently starting with an empty Skrivi directory.
            return legacy_path
    return path


def model_cache_directory(
    environment: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    env = _environment(environment)
    root = (
        Path(env["LOCALAPPDATA"])
        if env.get("LOCALAPPDATA")
        else _fallback_data_root(home)
    )
    path = _application_data_root(root) / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def settings_directory(
    development: bool = False,
    environment: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    env = _environment(environment)
    if env.get("APPDATA"):
        root = Path(env["APPDATA"])
    else:
        root = (home or Path.home()) / "AppData" / "Roaming"
    path = _application_data_root(root)
    if development:
        path /= "development"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_packaged_identity(directory: Path) -> BuildIdentity | None:
    path = directory / BUILD_INFO_FILENAME
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        identifier = str(data["build_id"]).strip()
        development = bool(data.get("development", False))
    except BUILD_INFO_ERRORS:
        return None
    if not identifier:
        return None
    return BuildIdentity(identifier=identifier, development=development)


def _source_commit(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "describe", "--always", "--dirty", "--abbrev=7"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except GIT_IDENTITY_ERRORS:
        return None
    identifier = result.stdout.strip()
    return identifier or None


def _package_version() -> str:
    try:
        return version("skrivi")
    except PackageNotFoundError:
        return "source"


def detect_build_identity(
    *,
    force_development: bool = False,
    environment: Mapping[str, str] | None = None,
    executable_directory: Path | None = None,
    repo_root: Path | None = None,
) -> BuildIdentity:
    env = _environment(environment)
    development = force_development or env.get("SKRIVI_DEVELOPMENT") == "1"
    explicit = env.get("SKRIVI_BUILD_ID", "").strip()
    if explicit:
        return BuildIdentity(identifier=explicit, development=development)

    if executable_directory is None and getattr(sys, "frozen", False):
        executable_directory = Path(sys.executable).resolve().parent
    if executable_directory is not None:
        packaged = _read_packaged_identity(executable_directory)
        if packaged is not None:
            if force_development:
                return BuildIdentity(packaged.identifier, development=True)
            return packaged

    if development:
        root = repo_root or Path(__file__).resolve().parents[2]
        commit = _source_commit(root)
        if commit:
            return BuildIdentity(identifier=commit, development=True)
    return BuildIdentity(identifier=_package_version(), development=development)
