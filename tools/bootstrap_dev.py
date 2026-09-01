from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = (
    ROOT / "pyproject.toml",
    ROOT / "requirements.txt",
    ROOT / "requirements-dev.txt",
    ROOT / "constraints-windows.txt",
)
MARKER = ROOT / ".venv" / ".skrivi-development-dependencies"
LEGACY_DISTRIBUTION = "whisper-dictate"


def dependency_fingerprint(paths: tuple[Path, ...] = INPUTS) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    fingerprint = dependency_fingerprint()
    if MARKER.exists() and MARKER.read_text(encoding="utf-8").strip() == fingerprint:
        print("Development dependencies are already current.")
        return

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(ROOT / "requirements-dev.txt"),
            "-c",
            str(ROOT / "constraints-windows.txt"),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "--yes", LEGACY_DISTRIBUTION],
        cwd=ROOT,
        check=False,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-e",
            str(ROOT),
            "-c",
            str(ROOT / "constraints-windows.txt"),
        ],
        cwd=ROOT,
        check=True,
    )
    MARKER.write_text(fingerprint + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
