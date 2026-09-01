from __future__ import annotations

import argparse
import ctypes
import os
import sys
from dataclasses import replace

from whisper_dictate.application import create_application
from whisper_dictate.audio import AudioRecorder, list_input_devices
from whisper_dictate.config import AppConfig
from whisper_dictate.controller import AppState, DictationController
from whisper_dictate.hotkeys import PushToTalkListener
from whisper_dictate.i18n import set_interface_language, tr
from whisper_dictate.indicator import FloatingIndicator
from whisper_dictate.lifecycle import shutdown_runtime
from whisper_dictate.model_runtime import ModelRuntime
from whisper_dictate.models import LocalModelManager
from whisper_dictate.runtime import detect_build_identity, model_cache_directory
from whisper_dictate.runtime_settings import RuntimeSettingsApplier
from whisper_dictate.settings import SettingsStore, SettingsWriteError
from whisper_dictate.settings_window import SettingsWindow
from whisper_dictate.transcriber import LocalWhisperTranscriber
from whisper_dictate.tray import TrayIcon
from whisper_dictate.windows_input import WindowsTextInjector


def _single_instance_mutex():
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
    kernel32.CloseHandle.restype = ctypes.c_bool
    mutexes = []
    already_exists = False
    # Holding the legacy name prevents an older build and Skrivi from both
    # owning the same global hotkey during the one-machine upgrade.
    for name in (
        "Local\\Skrivi-43D72B32",
        "Local\\WhisperDictate-43D72B32",
    ):
        mutex = kernel32.CreateMutexW(None, False, name)
        if not mutex:
            for existing in mutexes:
                kernel32.CloseHandle(existing)
            raise ctypes.WinError()
        mutexes.append(mutex)
        already_exists = kernel32.GetLastError() == 183 or already_exists
    return tuple(mutexes), already_exists


def _close_mutexes(mutexes) -> None:
    for mutex in mutexes:
        ctypes.windll.kernel32.CloseHandle(mutex)


def _arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Skrivi local dictation")
    parser.add_argument(
        "--development",
        action="store_true",
        help="Identify this process as a development build",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview indicator states without audio, Whisper, hotkeys or typing",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _arguments(argv)
    if os.name != "nt":
        print(tr("Skrivi runs on Windows 11."), file=sys.stderr)
        raise SystemExit(1)

    identity = detect_build_identity(force_development=args.development)
    settings_store = SettingsStore.for_user(development=identity.development)
    settings = settings_store.load().settings
    set_interface_language(settings.interface_language)
    if args.preview:
        from whisper_dictate.preview import run_preview

        run_preview(identity.title)
        return

    mutexes, already_exists = _single_instance_mutex()
    if already_exists:
        ctypes.windll.user32.MessageBoxW(
            None,
            tr("Skrivi is already running."),
            identity.title,
            0x40,
        )
        _close_mutexes(mutexes)
        return

    _application = create_application(identity.title)
    config = AppConfig(model_name=settings.model)
    indicator = FloatingIndicator(
        title=identity.title, enabled=settings.overlay_enabled
    )
    recorder = AudioRecorder(settings.microphone)
    model_cache = model_cache_directory()
    model_manager = LocalModelManager(model_cache)
    settings_applier = None

    def resolve_startup_model(requested: str):
        actual, path = model_manager.resolve_startup_model(requested)
        if actual != requested:
            corrected = replace(settings_store.load().settings, model=actual)
            try:
                settings_store.save(corrected)
            except SettingsWriteError:
                pass
            else:
                if settings_applier is not None:
                    settings_applier.sync_current(corrected)
        return actual, path

    transcriber = LocalWhisperTranscriber(
        config,
        model_cache,
        language=settings.language,
        model_name=settings.model,
        model_resolver=resolve_startup_model,
    )
    injector = WindowsTextInjector()

    controller = None

    def pressed() -> None:
        if controller is not None:
            controller.on_hotkey_press()

    def released() -> None:
        if controller is not None:
            controller.on_hotkey_release()

    def cancelled() -> None:
        if controller is not None:
            controller.cancel_current()

    listener = PushToTalkListener(
        pressed,
        released,
        settings.hotkey,
        on_cancel=cancelled,
    )
    controller = DictationController(
        config=config,
        recorder=recorder,
        transcriber=transcriber,
        injector=injector,
        indicator=indicator,
        hotkey_listener=listener,
    )
    settings_applier = RuntimeSettingsApplier(
        settings_store,
        settings,
        recorder,
        transcriber,
        listener,
        can_change_input=lambda: not recorder.is_recording,
    )
    model_runtime = ModelRuntime(
        model_manager,
        transcriber,
        settings_store,
        can_activate=lambda: controller.state is AppState.READY,
        settings_sync=settings_applier.sync_current,
    )
    settings_window = SettingsWindow(
        settings_store,
        title=identity.title,
        save_settings=settings_applier.apply,
        microphone_provider=list_input_devices,
        can_change_input=lambda: not recorder.is_recording,
        active_model=config.model_name,
        model_manager=model_manager,
        model_runtime=model_runtime,
    )
    tray = TrayIcon(
        indicator.request_exit,
        on_settings=settings_window.show_settings,
        on_retry_model=controller.retry_model_load,
        title=identity.title,
    )
    indicator.status_changed.connect(tray.set_status)
    indicator.status_changed.connect(settings_window.set_status)
    settings_window.settings_saved.connect(
        lambda saved: indicator.set_enabled(saved.overlay_enabled)
    )
    settings_window.hotkey_capture_started.connect(listener.stop)
    settings_window.hotkey_capture_finished.connect(listener.start)
    settings_window.model_panel.model_activated.connect(
        lambda _identifier: controller.retry_model_load()
    )

    def shutdown() -> None:
        shutdown_runtime(
            controller,
            model_manager,
            tray,
            lambda: _close_mutexes(mutexes),
        )

    indicator.set_exit_handler(shutdown)
    tray.start()
    controller.start()
    indicator.run()
