from __future__ import annotations

from pathlib import Path

import pytest

from whisper_dictate.platform_services import StartupRegistrationError
from whisper_dictate.windows_startup import (
    RUN_KEY,
    STARTUP_TASK_ID,
    VALUE_NAME,
    PackagedStartupState,
    PackagedWindowsStartupManager,
    WindowsStartupManager,
    reconcile_startup_preference,
    startup_manager_for_current_app,
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


class MemoryPackagedStartup:
    def __init__(self, state: PackagedStartupState) -> None:
        self.current = state
        self.requested: list[str] = []
        self.disabled: list[str] = []

    def state(self, task_id: str) -> PackagedStartupState:
        assert task_id == STARTUP_TASK_ID
        return self.current

    def request_enable(self, task_id: str) -> PackagedStartupState:
        self.requested.append(task_id)
        if self.current is PackagedStartupState.DISABLED:
            self.current = PackagedStartupState.ENABLED
        return self.current

    def disable(self, task_id: str) -> None:
        self.disabled.append(task_id)
        self.current = PackagedStartupState.DISABLED


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


def test_msix_build_uses_packaged_startup_task(monkeypatch) -> None:
    monkeypatch.setattr("whisper_dictate.windows_startup.os.name", "nt")
    monkeypatch.setattr(
        "whisper_dictate.windows_startup.sys.frozen", True, raising=False
    )

    manager = startup_manager_for_current_app(packaged=True)

    assert isinstance(manager, PackagedWindowsStartupManager)
    assert manager.available is True


def test_packaged_startup_can_be_enabled_and_disabled() -> None:
    backend = MemoryPackagedStartup(PackagedStartupState.DISABLED)
    manager = PackagedWindowsStartupManager(backend=backend)

    manager.set_enabled(True)

    assert manager.is_enabled() is True
    assert backend.requested == [STARTUP_TASK_ID]

    manager.set_enabled(False)

    assert manager.is_enabled() is False
    assert backend.disabled == [STARTUP_TASK_ID]


def test_packaged_startup_respects_a_user_disabled_task() -> None:
    manager = PackagedWindowsStartupManager(
        backend=MemoryPackagedStartup(PackagedStartupState.DISABLED_BY_USER)
    )

    with pytest.raises(StartupRegistrationError, match="Windows has disabled"):
        manager.set_enabled(True)

    assert reconcile_startup_preference(manager, requested=True) is False


@pytest.mark.parametrize(
    ("state", "enabled", "message"),
    [
        (
            PackagedStartupState.DISABLED_BY_POLICY,
            True,
            "disabled by your organisation",
        ),
        (
            PackagedStartupState.ENABLED_BY_POLICY,
            False,
            "required by your organisation",
        ),
    ],
)
def test_packaged_startup_respects_windows_policy(
    state: PackagedStartupState,
    enabled: bool,
    message: str,
) -> None:
    manager = PackagedWindowsStartupManager(backend=MemoryPackagedStartup(state))

    with pytest.raises(StartupRegistrationError, match=message):
        manager.set_enabled(enabled)


def test_packaged_startup_wraps_backend_errors() -> None:
    class FailingPackagedStartup(MemoryPackagedStartup):
        def state(self, task_id: str) -> PackagedStartupState:
            del task_id
            raise OSError("private Windows detail")

    manager = PackagedWindowsStartupManager(
        backend=FailingPackagedStartup(PackagedStartupState.DISABLED)
    )

    with pytest.raises(
        StartupRegistrationError,
        match="could not read Windows startup settings",
    ) as caught:
        manager.is_enabled()

    assert "private Windows detail" not in str(caught.value)


def test_unpacked_executable_keeps_registry_startup(monkeypatch, tmp_path) -> None:
    executable = tmp_path / "Skrivi.exe"
    monkeypatch.setattr("whisper_dictate.windows_startup.os.name", "nt")
    monkeypatch.setattr(
        "whisper_dictate.windows_startup.sys.frozen", True, raising=False
    )
    monkeypatch.setattr(
        "whisper_dictate.windows_startup.sys.executable", str(executable)
    )

    manager = startup_manager_for_current_app(packaged=False)

    assert isinstance(manager, WindowsStartupManager)
    assert manager.command == f'"{executable.resolve()}"'
