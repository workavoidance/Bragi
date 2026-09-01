from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"


def source_snapshot(
    source_root: Path = SOURCE_ROOT,
) -> tuple[tuple[str, int, int], ...]:
    files = []
    for path in sorted(source_root.rglob("*.py")):
        stat = path.stat()
        files.append(
            (path.relative_to(source_root).as_posix(), stat.st_mtime_ns, stat.st_size)
        )
    return tuple(files)


def source_changed(
    previous: tuple[tuple[str, int, int], ...],
    current: tuple[tuple[str, int, int], ...],
) -> bool:
    return previous != current


def application_command(mode: str, executable: str = sys.executable) -> list[str]:
    command = [executable, "-m", "whisper_dictate", "--development"]
    if mode == "preview":
        command.append("--preview")
    return command


def start_child(mode: str) -> subprocess.Popen:
    environment = os.environ.copy()
    environment["SKRIVI_DEVELOPMENT"] = "1"
    return subprocess.Popen(
        application_command(mode),
        cwd=ROOT,
        env=environment,
    )


def stop_child(child: subprocess.Popen, timeout_seconds: float = 5.0) -> None:
    if child.poll() is not None:
        return
    child.terminate()
    try:
        child.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait()


def run(mode: str, poll_seconds: float = 0.5) -> None:
    print(f"Starting Skrivi development mode: {mode}")
    print("Source changes restart the managed app. Press Ctrl+C to stop.")
    previous = source_snapshot()
    child = start_child(mode)
    try:
        while True:
            time.sleep(poll_seconds)
            current = source_snapshot()
            if not source_changed(previous, current):
                continue
            print("Source changed. Restarting Skrivi...")
            stop_child(child)
            previous = current
            child = start_child(mode)
    except KeyboardInterrupt:
        print("Stopping Skrivi development mode...")
    finally:
        stop_child(child)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run and restart Skrivi from source")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=("real", "preview"),
        default="real",
        help="Use 'preview' to avoid Whisper, microphone, hotkey and text input",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    arguments = parse_args()
    run(arguments.mode)
