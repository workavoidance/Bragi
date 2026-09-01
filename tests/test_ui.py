from __future__ import annotations

import os
import threading
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import QApplication

from whisper_dictate.application import create_application
from whisper_dictate.indicator import FloatingIndicator, overlay_position
from whisper_dictate.settings import LanguageMode, SettingsStore, UserSettings
from whisper_dictate.settings_window import (
    HotkeyCaptureButton,
    SettingsWindow,
    hotkey_from_qt_key,
)
from whisper_dictate.tray import TrayIcon


def application() -> QApplication:
    return create_application("Bragi tests")


def process_events_until(predicate, timeout: float = 1.0) -> None:
    deadline = time.monotonic() + timeout
    app = application()
    while time.monotonic() < deadline and not predicate():
        app.processEvents()
        time.sleep(0.005)


def test_overlay_position_handles_displays_on_either_side() -> None:
    assert overlay_position((1920, 0, 2560, 1400), (360, 70)) == (3020, 1266)
    assert overlay_position((-1920, -100, 1920, 1080), (360, 70)) == (-1140, 846)
    assert overlay_position((50, 75, 200, 100), (360, 120)) == (50, 75)


def test_indicator_is_non_activating_and_worker_safe() -> None:
    application()
    indicator = FloatingIndicator(enabled=False)
    received: list[tuple[str, str]] = []
    indicator.status_changed.connect(lambda state, text: received.append((state, text)))

    worker = threading.Thread(target=lambda: indicator.post("transcribing"))
    worker.start()
    worker.join()
    process_events_until(lambda: bool(received))

    assert received == [("transcribing", "Transcribing locally…")]
    assert indicator.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus
    assert indicator.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    assert indicator.accessibleName() == "Bragi dictation status"


def test_settings_window_saves_overlay_choice(tmp_path: Path) -> None:
    application()
    store = SettingsStore(tmp_path / "settings.json")
    store.save(UserSettings(overlay_enabled=True))
    window = SettingsWindow(store)
    saved: list[UserSettings] = []
    window.settings_saved.connect(saved.append)

    window.overlay_checkbox.setChecked(False)
    window._save()

    assert store.load().settings.overlay_enabled is False
    assert saved == [UserSettings(overlay_enabled=False)]


def test_settings_window_saves_live_language_and_hotkey_choices(tmp_path: Path) -> None:
    application()
    store = SettingsStore(tmp_path / "settings.json")
    applied: list[UserSettings] = []
    window = SettingsWindow(store, save_settings=applied.append)

    window.language_combo.setCurrentIndex(
        window.language_combo.findData(LanguageMode.NORWEGIAN.value)
    )
    window._set_hotkey("f8")
    window._save()

    assert applied == [UserSettings(language=LanguageMode.NORWEGIAN, hotkey="f8")]


def test_hotkey_capture_translation_accepts_only_safe_keys() -> None:
    assert hotkey_from_qt_key(int(Qt.Key.Key_Control), 0xA3) == "right_ctrl"
    assert hotkey_from_qt_key(int(Qt.Key.Key_Alt), 0xA5) == "right_alt"
    assert hotkey_from_qt_key(int(Qt.Key.Key_Control), 0x11, 0xE01D) == ("right_ctrl")
    assert hotkey_from_qt_key(int(Qt.Key.Key_Alt), 0x12, 0xE038) == "right_alt"
    assert hotkey_from_qt_key(int(Qt.Key.Key_Control), 0x11, 0x1D) is None
    assert hotkey_from_qt_key(int(Qt.Key.Key_Alt), 0x12, 0x38) is None
    assert hotkey_from_qt_key(int(Qt.Key.Key_F8), 0) == "f8"
    assert hotkey_from_qt_key(int(Qt.Key.Key_A), 0) is None


def test_hotkey_capture_is_blocked_during_a_recording() -> None:
    application()
    button = HotkeyCaptureButton(can_capture=lambda: False)
    messages: list[str] = []
    button.capture_rejected.connect(messages.append)

    button.begin_capture()

    assert button.is_capturing is False
    assert messages == [
        "Finish the current recording before changing the push-to-talk key."
    ]


def test_hotkey_listener_restarts_only_after_captured_key_is_released() -> None:
    application()
    button = HotkeyCaptureButton()
    events: list[str] = []
    button.capture_started.connect(lambda: events.append("listener stopped"))
    button.hotkey_captured.connect(lambda key: events.append(f"captured {key}"))
    button.capture_finished.connect(lambda: events.append("listener started"))

    button.begin_capture()
    press = QKeyEvent(
        QEvent.Type.KeyPress,
        Qt.Key.Key_F8,
        Qt.KeyboardModifier.NoModifier,
    )
    button.keyPressEvent(press)

    assert button.is_capturing is True
    assert events == ["listener stopped", "captured f8"]

    release = QKeyEvent(
        QEvent.Type.KeyRelease,
        Qt.Key.Key_F8,
        Qt.KeyboardModifier.NoModifier,
    )
    button.keyReleaseEvent(release)

    assert button.is_capturing is False
    assert events == ["listener stopped", "captured f8", "listener started"]


def test_settings_actions_are_named_and_keyboard_operable(tmp_path: Path) -> None:
    application()
    window = SettingsWindow(SettingsStore(tmp_path / "settings.json"))

    assert window.accessibleName() == "Bragi settings"
    assert window.tabs.accessibleName() == "Settings sections"
    assert window.overlay_checkbox.accessibleName() == ("Show dictation status overlay")
    assert window.language_combo.accessibleName() == "Dictation language"
    assert window.microphone_combo.accessibleName() == "Microphone"
    assert window.model_panel.accessibleName() == "Local speech models"
    assert window.model_panel.model_combo.accessibleName() == "Speech model"
    assert window.model_panel.download_button.isEnabled() is False
    assert window.overlay_checkbox.focusPolicy() & Qt.FocusPolicy.TabFocus
    assert window.save_shortcut.key().matches(QKeySequence.StandardKey.Save) == (
        QKeySequence.SequenceMatch.ExactMatch
    )


def test_tray_exposes_status_settings_and_exit() -> None:
    application()
    events: list[str] = []
    tray = TrayIcon(
        lambda: events.append("exit"),
        on_settings=lambda: events.append("settings"),
    )

    texts = [action.text().replace("&", "") for action in tray.menu.actions()]
    assert "Status: Starting" in texts
    assert "Settings…" in texts
    assert "Exit" in texts

    tray.settings_action.trigger()
    tray.exit_action.trigger()
    assert events == ["settings", "exit"]
