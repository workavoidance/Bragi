from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path
from typing import Protocol

from whisper_dictate.platform_services import (
    StartupManager,
    StartupRegistrationError,
    UnavailableStartupManager,
)

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "Skrivi"
APPMODEL_ERROR_NO_PACKAGE = 15700


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


def startup_manager_for_current_app(*, packaged: bool | None = None) -> StartupManager:
    """Return startup support only where Windows registry startup is effective."""
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return UnavailableStartupManager()
    if packaged is None:
        packaged = _running_with_package_identity()
    if packaged:
        # HKCU writes are virtualized for MSIX applications and therefore do
        # not register a real Windows startup entry. Keep the setting disabled
        # until Skrivi adopts the packaged StartupTask API.
        return UnavailableStartupManager()
    return WindowsStartupManager(Path(sys.executable))
