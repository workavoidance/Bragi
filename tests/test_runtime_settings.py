from __future__ import annotations

from dataclasses import replace

import pytest

from whisper_dictate.audio import MicrophoneUnavailableError
from whisper_dictate.platform_services import StartupRegistrationError
from whisper_dictate.runtime_settings import (
    RuntimeSettingsApplier,
    RuntimeSettingsError,
)
from whisper_dictate.settings import LanguageMode, SettingsStore, UserSettings


class FakeRecorder:
    def __init__(self) -> None:
        self.microphone = "windows_default"
        self.validated: list[str] = []

    def validate_microphone(self, identifier: str) -> None:
        self.validated.append(identifier)
        if identifier.endswith("missing"):
            raise MicrophoneUnavailableError("Choose Windows Default.")

    def set_microphone(self, identifier: str) -> None:
        self.microphone = identifier


class FakeTranscriber:
    def __init__(self) -> None:
        self.language = LanguageMode.AUTOMATIC

    def set_language_mode(self, language: LanguageMode) -> None:
        self.language = language


class FakeHotkey:
    def __init__(self) -> None:
        self.hotkey = "right_ctrl"
        self.replacements: list[str] = []

    def replace_hotkey(self, identifier: str) -> None:
        self.replacements.append(identifier)
        self.hotkey = identifier


class FakeStartupManager:
    available = True

    def __init__(self) -> None:
        self.enabled = False
        self.changes: list[bool] = []

    def is_enabled(self) -> bool:
        return self.enabled

    def set_enabled(self, enabled: bool) -> None:
        self.changes.append(enabled)
        self.enabled = enabled


def make_applier(
    tmp_path,
    *,
    can_change_input=lambda: True,
    startup_manager=None,
):
    store = SettingsStore(tmp_path / "settings.json")
    initial = UserSettings()
    store.save(initial)
    recorder = FakeRecorder()
    transcriber = FakeTranscriber()
    hotkey = FakeHotkey()
    applier = RuntimeSettingsApplier(
        store,
        initial,
        recorder,
        transcriber,
        hotkey,
        can_change_input=can_change_input,
        startup_manager=startup_manager,
    )
    return applier, store, recorder, transcriber, hotkey


def test_runtime_settings_apply_and_persist_as_one_operation(tmp_path) -> None:
    applier, store, recorder, transcriber, hotkey = make_applier(tmp_path)
    updated = replace(
        UserSettings(),
        language=LanguageMode.NORWEGIAN,
        microphone="portaudio:WASAPI:USB%20mic",
        hotkey="f8",
    )

    applier.apply(updated)

    assert applier.current == updated
    assert store.load().settings == updated
    assert recorder.microphone == updated.microphone
    assert transcriber.language is LanguageMode.NORWEGIAN
    assert hotkey.hotkey == "f8"


def test_input_changes_are_blocked_during_recording(tmp_path) -> None:
    applier, _store, recorder, _transcriber, hotkey = make_applier(
        tmp_path, can_change_input=lambda: False
    )

    with pytest.raises(RuntimeSettingsError, match="Finish the current recording"):
        applier.apply(replace(UserSettings(), hotkey="f8"))

    assert recorder.microphone == "windows_default"
    assert hotkey.hotkey == "right_ctrl"


def test_disconnected_microphone_does_not_change_active_settings(tmp_path) -> None:
    applier, store, recorder, transcriber, hotkey = make_applier(tmp_path)

    with pytest.raises(RuntimeSettingsError, match="Windows Default"):
        applier.apply(replace(UserSettings(), microphone="portaudio:WASAPI:missing"))

    assert applier.current == UserSettings()
    assert store.load().settings == UserSettings()
    assert recorder.microphone == "windows_default"
    assert transcriber.language is LanguageMode.AUTOMATIC
    assert hotkey.hotkey == "right_ctrl"


def test_save_failure_rolls_back_all_live_choices(tmp_path, monkeypatch) -> None:
    applier, store, recorder, transcriber, hotkey = make_applier(tmp_path)
    updated = replace(
        UserSettings(),
        language=LanguageMode.NORWEGIAN,
        microphone="portaudio:WASAPI:USB%20mic",
        hotkey="f8",
    )

    def fail_save(settings) -> None:
        del settings
        raise OSError("simulated write failure")

    monkeypatch.setattr(store, "save", fail_save)

    with pytest.raises(OSError, match="simulated write failure"):
        applier.apply(updated)

    assert applier.current == UserSettings()
    assert recorder.microphone == "windows_default"
    assert transcriber.language is LanguageMode.AUTOMATIC
    assert hotkey.hotkey == "right_ctrl"
    assert hotkey.replacements == ["f8", "right_ctrl"]


def test_runtime_settings_apply_automatic_startup(tmp_path) -> None:
    startup = FakeStartupManager()
    applier, store, _recorder, _transcriber, _hotkey = make_applier(
        tmp_path, startup_manager=startup
    )

    updated = replace(UserSettings(), start_with_system=True)
    applier.apply(updated)

    assert startup.enabled is True
    assert startup.changes == [True]
    assert store.load().settings.start_with_system is True


def test_startup_failure_preserves_previous_settings(tmp_path) -> None:
    class FailingStartupManager(FakeStartupManager):
        def set_enabled(self, enabled: bool) -> None:
            del enabled
            raise StartupRegistrationError("startup failed")

    startup = FailingStartupManager()
    applier, store, _recorder, _transcriber, _hotkey = make_applier(
        tmp_path, startup_manager=startup
    )

    with pytest.raises(RuntimeSettingsError, match="startup failed"):
        applier.apply(replace(UserSettings(), start_with_system=True))

    assert store.load().settings == UserSettings()


def test_startup_failure_rolls_back_a_hotkey_changed_in_the_same_save(tmp_path) -> None:
    class FailingStartupManager(FakeStartupManager):
        def set_enabled(self, enabled: bool) -> None:
            del enabled
            raise StartupRegistrationError("startup failed")

    applier, store, _recorder, _transcriber, hotkey = make_applier(
        tmp_path, startup_manager=FailingStartupManager()
    )

    with pytest.raises(RuntimeSettingsError, match="startup failed"):
        applier.apply(replace(UserSettings(), hotkey="f8", start_with_system=True))

    assert hotkey.hotkey == "right_ctrl"
    assert hotkey.replacements == ["f8", "right_ctrl"]
    assert store.load().settings == UserSettings()


def test_save_failure_rolls_back_automatic_startup(tmp_path, monkeypatch) -> None:
    startup = FakeStartupManager()
    applier, store, _recorder, _transcriber, _hotkey = make_applier(
        tmp_path, startup_manager=startup
    )

    def fail_save(settings) -> None:
        del settings
        raise OSError("simulated write failure")

    monkeypatch.setattr(store, "save", fail_save)

    with pytest.raises(OSError, match="simulated write failure"):
        applier.apply(replace(UserSettings(), start_with_system=True))

    assert startup.enabled is False
    assert startup.changes == [True, False]
