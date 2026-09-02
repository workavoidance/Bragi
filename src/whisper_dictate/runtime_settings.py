from __future__ import annotations

from collections.abc import Callable

from whisper_dictate.audio import MicrophoneUnavailableError
from whisper_dictate.hotkeys import HotkeyActivationError
from whisper_dictate.i18n import tr
from whisper_dictate.platform_services import (
    StartupManager,
    StartupRegistrationError,
    UnavailableStartupManager,
)
from whisper_dictate.settings import SettingsStore, UserSettings


class RuntimeSettingsError(ValueError):
    """Raised when settings cannot safely become active."""


class RuntimeSettingsApplier:
    """Apply runtime choices and persist them as one recoverable operation."""

    def __init__(
        self,
        store: SettingsStore,
        initial: UserSettings,
        recorder,
        transcriber,
        hotkey_listener,
        *,
        can_change_input: Callable[[], bool] | None = None,
        startup_manager: StartupManager | None = None,
    ) -> None:
        self._store = store
        self._current = initial
        self._recorder = recorder
        self._transcriber = transcriber
        self._hotkey_listener = hotkey_listener
        self._can_change_input = can_change_input or (lambda: True)
        self._startup_manager = startup_manager or UnavailableStartupManager()

    @property
    def current(self) -> UserSettings:
        return self._current

    def sync_current(self, settings: UserSettings) -> None:
        """Adopt settings persisted by another coordinated runtime feature."""
        self._current = UserSettings.from_document(settings.to_document())

    def apply(self, settings: UserSettings) -> None:
        updated = UserSettings.from_document(settings.to_document())
        previous = self._current
        microphone_changed = updated.microphone != previous.microphone
        hotkey_changed = updated.hotkey != previous.hotkey
        startup_changed = updated.start_with_system != previous.start_with_system
        if (microphone_changed or hotkey_changed) and not self._can_change_input():
            raise RuntimeSettingsError(
                tr(
                    "Finish the current recording before changing the microphone or "
                    "push-to-talk key."
                )
            )
        if microphone_changed:
            try:
                self._recorder.validate_microphone(updated.microphone)
            except MicrophoneUnavailableError as error:
                raise RuntimeSettingsError(str(error)) from error

        hotkey_applied = False
        startup_applied = False
        try:
            if hotkey_changed:
                self._hotkey_listener.replace_hotkey(updated.hotkey)
                hotkey_applied = True
            if startup_changed:
                self._startup_manager.set_enabled(updated.start_with_system)
                startup_applied = True
            self._transcriber.set_language_mode(updated.language)
            self._recorder.set_microphone(updated.microphone)
            self._store.save(updated)
        except Exception as error:
            self._transcriber.set_language_mode(previous.language)
            self._recorder.set_microphone(previous.microphone)
            if hotkey_applied:
                try:
                    self._hotkey_listener.replace_hotkey(previous.hotkey)
                except HotkeyActivationError:
                    pass
            if startup_applied:
                try:
                    self._startup_manager.set_enabled(previous.start_with_system)
                except StartupRegistrationError:
                    pass
            if isinstance(error, (HotkeyActivationError, StartupRegistrationError)):
                raise RuntimeSettingsError(tr(str(error))) from error
            raise
        self._current = updated
