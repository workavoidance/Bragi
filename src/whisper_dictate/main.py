from __future__ import annotations

import ctypes
import os
import sys

from whisper_dictate.audio import AudioRecorder
from whisper_dictate.config import AppConfig, model_cache_directory
from whisper_dictate.controller import DictationController
from whisper_dictate.hotkeys import RightControlListener
from whisper_dictate.indicator import FloatingIndicator
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


def main() -> None:
    if os.name != "nt":
        print("Whisper Dictate runs on Windows 11.", file=sys.stderr)
        raise SystemExit(1)

    mutex, already_exists = _single_instance_mutex()
    if already_exists:
        ctypes.windll.user32.MessageBoxW(
            None,
            "Whisper Dictate is already running.",
            "Whisper Dictate",
            0x40,
        )
        ctypes.windll.kernel32.CloseHandle(mutex)
        return

    config = AppConfig()
    indicator = FloatingIndicator()
    recorder = AudioRecorder()
    transcriber = LocalWhisperTranscriber(config, model_cache_directory())
    injector = WindowsTextInjector()

    controller = None

    def pressed() -> None:
        if controller is not None:
            controller.on_hotkey_press()

    def released() -> None:
        if controller is not None:
            controller.on_hotkey_release()

    listener = RightControlListener(pressed, released)
    controller = DictationController(
        config=config,
        recorder=recorder,
        transcriber=transcriber,
        injector=injector,
        indicator=indicator,
        hotkey_listener=listener,
    )
    tray = TrayIcon(indicator.request_exit)

    def shutdown() -> None:
        controller.stop()
        tray.stop()
        ctypes.windll.kernel32.CloseHandle(mutex)

    indicator.set_exit_handler(shutdown)
    tray.start()
    controller.start()
    indicator.run()
