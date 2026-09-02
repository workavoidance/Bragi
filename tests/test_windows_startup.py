from __future__ import annotations

from pathlib import Path

import pytest

from whisper_dictate.platform_services import StartupRegistrationError
from whisper_dictate.windows_startup import (
    RUN_KEY,
    VALUE_NAME,
    WindowsStartupManager,
)


class MemoryRegistry:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def read(self, key: str, name: str) -> str | None:
        return self.values.get((key, name))

    def write(self, key: str, name: str, value: str) -> None:
        self.values[(key, name)] = value

    def delete(self, key: str, name: str) -> None:
        self.values.pop((key, name), None)


def test_windows_startup_quotes_and_registers_the_exact_executable(tmp_path) -> None:
    executable = tmp_path / "Permanent Folder" / "Skrivi.exe"
    registry = MemoryRegistry()
    manager = WindowsStartupManager(executable, registry=registry)

    manager.set_enabled(True)

    assert registry.values[(RUN_KEY, VALUE_NAME)] == f'"{executable.resolve()}"'
    assert manager.is_enabled() is True


def test_windows_startup_detects_a_moved_portable_executable(tmp_path) -> None:
    registry = MemoryRegistry()
    original = WindowsStartupManager(tmp_path / "old" / "Skrivi.exe", registry=registry)
    moved = WindowsStartupManager(tmp_path / "new" / "Skrivi.exe", registry=registry)
    original.set_enabled(True)

    assert moved.is_enabled() is False

    moved.set_enabled(True)

    assert moved.is_enabled() is True


def test_disabling_startup_is_idempotent(tmp_path) -> None:
    registry = MemoryRegistry()
    manager = WindowsStartupManager(tmp_path / "Skrivi.exe", registry=registry)

    manager.set_enabled(False)
    manager.set_enabled(True)
    manager.set_enabled(False)

    assert manager.is_enabled() is False


def test_registry_errors_are_reported_without_exposing_the_path(tmp_path) -> None:
    class FailingRegistry(MemoryRegistry):
        def write(self, key: str, name: str, value: str) -> None:
            del key, name, value
            raise OSError("private registry detail")

    manager = WindowsStartupManager(
        Path(tmp_path / "Private Name" / "Skrivi.exe"), registry=FailingRegistry()
    )

    with pytest.raises(StartupRegistrationError) as caught:
        manager.set_enabled(True)

    assert str(tmp_path) not in str(caught.value)
    assert "private registry detail" not in str(caught.value)
