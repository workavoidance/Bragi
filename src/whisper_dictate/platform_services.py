from __future__ import annotations

from typing import Protocol


class StartupRegistrationError(OSError):
    """Raised when automatic startup cannot be changed safely."""


class StartupManager(Protocol):
    """Platform boundary for starting Skrivi when the user signs in."""

    @property
    def available(self) -> bool: ...

    def is_enabled(self) -> bool: ...

    def set_enabled(self, enabled: bool) -> None: ...


class UnavailableStartupManager:
    """Safe fallback for source runs and future unsupported platforms."""

    @property
    def available(self) -> bool:
        return False

    def is_enabled(self) -> bool:
        return False

    def set_enabled(self, enabled: bool) -> None:
        if enabled:
            raise StartupRegistrationError(
                "Automatic startup is unavailable in this Skrivi build."
            )
