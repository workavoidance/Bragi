from __future__ import annotations

import argparse
import ctypes
import os
import sys

from whisper_dictate.application import create_application
from whisper_dictate.audio import AudioRecorder, list_input_devices
from whisper_dictate.config import AppConfig
from whisper_dictate.controller import DictationController
from whisper_dictate.hotkeys import PushToTalkListener
from whisper_dictate.indicator import FloatingIndicator
from whisper_dictate.runtime import detect_build_identity, model_cache_directory
from whisper_dictate.runtime_settings import RuntimeSettingsApplier
from whisper_dictate.settings import SettingsStore
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
    mutex = kernel32.CreateMutexW(None, False, "Local\\WhisperDictate-43D72B32")
    if not mutex:
        raise ctypes.WinError()
    already_exists = kernel32.GetLastError() == 183
    return mutex, already_exists


def _arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bragi local dictation")
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
        print("Bragi runs on Windows 11.", file=sys.stderr)
        raise SystemExit(1)

    identity = detect_build_identity(force_development=args.development)
    if args.preview:
        from whisper_dictate.preview import run_preview

        run_preview(identity.title)
        return

    mutex, already_exists = _single_instance_mutex()
    if already_exists:
        ctypes.windll.user32.MessageBoxW(
            None,
            "Bragi is already running.",
            identity.title,
            0x40,
        )
        ctypes.windll.kernel32.CloseHandle(mutex)
        return

    _application = create_application(identity.title)
    settings_store = SettingsStore.for_user(development=identity.development)
    settings = settings_store.load().settings

    config = AppConfig()
    indicator = FloatingIndicator(
        title=identity.title, enabled=settings.overlay_enabled
    )
    recorder = AudioRecorder(settings.microphone)
    transcriber = LocalWhisperTranscriber(
        config, model_cache_directory(), language=settings.language
    )
    injector = WindowsTextInjector()

    controller = None

    def pressed() -> None:
        if controller is not None:
            controller.on_hotkey_press()

    def released() -> None:
        if controller is not None:
            controller.on_hotkey_release()

    listener = PushToTalkListener(pressed, released, settings.hotkey)
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
    settings_window = SettingsWindow(
        settings_store,
        title=identity.title,
        save_settings=settings_applier.apply,
        microphone_provider=list_input_devices,
        can_change_input=lambda: not recorder.is_recording,
        active_model=config.model_name,
    )
    tray = TrayIcon(
        indicator.request_exit,
        on_settings=settings_window.show_settings,
        title=identity.title,
    )
    indicator.status_changed.connect(tray.set_status)
    indicator.status_changed.connect(settings_window.set_status)
    settings_window.settings_saved.connect(
        lambda saved: indicator.set_enabled(saved.overlay_enabled)
    )
    settings_window.hotkey_capture_started.connect(listener.stop)
    settings_window.hotkey_capture_finished.connect(listener.start)

    def shutdown() -> None:
        controller.stop()
        tray.stop()
        ctypes.windll.kernel32.CloseHandle(mutex)

    indicator.set_exit_handler(shutdown)
    tray.start()
    controller.start()
    indicator.run()
