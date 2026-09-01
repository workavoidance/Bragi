from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from whisper_dictate.i18n import tr
from whisper_dictate.models import LocalModelManager, ModelState, ModelStatus
from whisper_dictate.settings import SettingsStore, UserSettings


class ModelActivationError(RuntimeError):
    """Raised when a model cannot safely replace the active model."""


class ModelRuntime:
    """Coordinate verified model loading, settings persistence, and rollback."""

    def __init__(
        self,
        manager: LocalModelManager,
        transcriber,
        store: SettingsStore,
        *,
        can_activate: Callable[[], bool] | None = None,
        settings_sync: Callable[[UserSettings], None] | None = None,
    ) -> None:
        self.manager = manager
        self.transcriber = transcriber
        self.store = store
        self._can_activate = can_activate or (lambda: True)
        self._settings_sync = settings_sync

    @property
    def active_model(self) -> str:
        return self.transcriber.active_model

    @staticmethod
    def _report(callback, status: ModelStatus) -> None:
        if callback is None:
            return
        try:
            callback(status)
        except Exception:
            pass

    def activate(
        self,
        identifier: str,
        callback: Callable[[ModelStatus], None] | None = None,
    ) -> None:
        spec = self.manager.spec(identifier)
        if identifier == self.active_model:
            return
        if not self._can_activate():
            raise ModelActivationError(
                tr("Wait until Skrivi is ready before changing the speech model.")
            )
        path = self.manager.verify_installed(identifier, thorough=True)
        self._report(
            callback,
            ModelStatus(
                identifier,
                ModelState.LOADING,
                None,
                tr("Loading {name} locally…", name=spec.name),
            ),
        )
        try:
            previous = self.transcriber.switch_model(identifier, path)
        except Exception as error:
            raise ModelActivationError(
                tr(
                    "{name} could not be loaded. The previous model is still active.",
                    name=spec.name,
                )
            ) from error

        current = self.store.load().settings
        updated = replace(current, model=identifier)
        try:
            self.store.save(updated)
        except Exception:
            self.transcriber.restore_model(previous)
            raise
        if self._settings_sync is not None:
            self._settings_sync(updated)
        self._report(
            callback,
            ModelStatus(
                identifier,
                ModelState.INSTALLED,
                1.0,
                tr("{name} is active.", name=spec.name),
            ),
        )
