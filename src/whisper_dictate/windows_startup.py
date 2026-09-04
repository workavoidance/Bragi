from __future__ import annotations

import asyncio
import ctypes
import os
import sys
from enum import IntEnum
from pathlib import Path
from typing import Any, Protocol

from whisper_dictate.platform_services import (
    StartupManager,
    StartupRegistrationError,
    UnavailableStartupManager,
)

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "Skrivi"
STARTUP_TASK_ID = "SkriviStartup"
APPMODEL_ERROR_NO_PACKAGE = 15700


class PackagedStartupState(IntEnum):
    DISABLED = 0
    DISABLED_BY_USER = 1
    ENABLED = 2
    DISABLED_BY_POLICY = 3
    ENABLED_BY_POLICY = 4


class RegistryBackend(Protocol):
    def read(self, key: str, name: str) -> str | None: ...

    def write(self, key: str, name: str, value: str) -> None: ...

    def delete(self, key: str, name: str) -> None: ...


class _WindowsRegistryBackend:
    def read(self, key: str, name: str) -> str | None:
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
                value, value_type = winreg.QueryValueEx(handle, name)
        except FileNotFoundError:
            return None
        if value_type not in {winreg.REG_SZ, winreg.REG_EXPAND_SZ}:
            return None
        return str(value)

    def write(self, key: str, name: str, value: str) -> None:
        import winreg

        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            key,
            0,
            winreg.KEY_SET_VALUE,
        ) as handle:
            winreg.SetValueEx(handle, name, 0, winreg.REG_SZ, value)

    def delete(self, key: str, name: str) -> None:
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key,
                0,
                winreg.KEY_SET_VALUE,
            ) as handle:
                winreg.DeleteValue(handle, name)
        except FileNotFoundError:
            return


class PackagedStartupBackend(Protocol):
    def state(self, task_id: str) -> PackagedStartupState: ...

    def request_enable(self, task_id: str) -> PackagedStartupState: ...

    def disable(self, task_id: str) -> None: ...


async def _await_operation(operation: Any) -> Any:
    return await operation


def _wait_for_operation(operation: Any) -> Any:
    return asyncio.run(_await_operation(operation))


class _WinRTPackagedStartupBackend:
    @staticmethod
    def _task(task_id: str):
        from winrt.windows.applicationmodel import StartupTask

        return _wait_for_operation(StartupTask.get_async(task_id))

    def state(self, task_id: str) -> PackagedStartupState:
        return PackagedStartupState(int(self._task(task_id).state))

    def request_enable(self, task_id: str) -> PackagedStartupState:
        task = self._task(task_id)
        return PackagedStartupState(
            int(_wait_for_operation(task.request_enable_async()))
        )

    def disable(self, task_id: str) -> None:
        self._task(task_id).disable()


class WindowsStartupManager:
    """Register a packaged Skrivi executable for the current Windows user."""

    def __init__(
        self,
        executable: Path,
        *,
        registry: RegistryBackend | None = None,
    ) -> None:
        self._executable = executable.resolve()
        self._registry = registry or _WindowsRegistryBackend()

    @property
    def available(self) -> bool:
        return True

    @property
    def command(self) -> str:
        # Windows paths cannot contain a quote. Always quoting the executable
        # prevents a path containing spaces from being split at sign-in.
        return f'"{self._executable}"'

    def is_enabled(self) -> bool:
        try:
            registered = self._registry.read(RUN_KEY, VALUE_NAME)
        except OSError as error:
            raise StartupRegistrationError(
                "Skrivi could not read Windows startup settings."
            ) from error
        return (
            registered is not None and registered.casefold() == self.command.casefold()
        )

    def set_enabled(self, enabled: bool) -> None:
        try:
            if enabled:
                self._registry.write(RUN_KEY, VALUE_NAME, self.command)
            else:
                self._registry.delete(RUN_KEY, VALUE_NAME)
        except OSError as error:
            raise StartupRegistrationError(
                "Skrivi could not change Windows startup settings."
            ) from error


class PackagedWindowsStartupManager:
    """Control the MSIX startup task declared in Skrivi's package manifest."""

    def __init__(
        self,
        *,
        task_id: str = STARTUP_TASK_ID,
        backend: PackagedStartupBackend | None = None,
    ) -> None:
        self._task_id = task_id
        self._backend = backend or _WinRTPackagedStartupBackend()

    @property
    def available(self) -> bool:
        return True

    def is_enabled(self) -> bool:
        try:
            state = self._backend.state(self._task_id)
        except Exception as error:
            raise StartupRegistrationError(
                "Skrivi could not read Windows startup settings."
            ) from error
        return state in {
            PackagedStartupState.ENABLED,
            PackagedStartupState.ENABLED_BY_POLICY,
        }

    def set_enabled(self, enabled: bool) -> None:
        try:
            state = self._backend.state(self._task_id)
            if enabled:
                if state in {
                    PackagedStartupState.ENABLED,
                    PackagedStartupState.ENABLED_BY_POLICY,
                }:
                    return
                if state is PackagedStartupState.DISABLED_BY_USER:
                    raise StartupRegistrationError(
                        "Windows has disabled Skrivi at startup. Enable it in "
                        "Windows Startup settings, then try again."
                    )
                if state is PackagedStartupState.DISABLED_BY_POLICY:
                    raise StartupRegistrationError(
                        "Automatic startup is disabled by your organisation's "
                        "Windows policy."
                    )
                state = self._backend.request_enable(self._task_id)
                if state not in {
                    PackagedStartupState.ENABLED,
                    PackagedStartupState.ENABLED_BY_POLICY,
                }:
                    raise StartupRegistrationError(
                        "Windows did not enable Skrivi at startup."
                    )
                return

            if state is PackagedStartupState.ENABLED_BY_POLICY:
                raise StartupRegistrationError(
                    "Automatic startup is required by your organisation's "
                    "Windows policy."
                )
            if state is PackagedStartupState.ENABLED:
                self._backend.disable(self._task_id)
        except StartupRegistrationError:
            raise
        except Exception as error:
            raise StartupRegistrationError(
                "Skrivi could not change Windows startup settings."
            ) from error


def _running_with_package_identity() -> bool:
    if os.name != "nt":
        return False
    try:
        length = ctypes.c_uint32()
        result = ctypes.windll.kernel32.GetCurrentPackageFullName(
            ctypes.byref(length), None
        )
    except AttributeError, OSError:
        return False
    return result != APPMODEL_ERROR_NO_PACKAGE


def reconcile_startup_preference(
    manager: StartupManager,
    requested: bool,
) -> bool:
    """Apply a saved preference and return Windows' authoritative state."""
    if not manager.available:
        return requested
    if requested:
        try:
            # This also repairs a registry command after an unpackaged portable
            # executable is deliberately moved to a new permanent folder.
            manager.set_enabled(True)
        except OSError:
            pass
    try:
        return manager.is_enabled()
    except OSError:
        return requested


def startup_manager_for_current_app(*, packaged: bool | None = None) -> StartupManager:
    """Return the startup implementation for the current Windows build."""
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return UnavailableStartupManager()
    if packaged is None:
        packaged = _running_with_package_identity()
    if packaged:
        return PackagedWindowsStartupManager()
    return WindowsStartupManager(Path(sys.executable))
