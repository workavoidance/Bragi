from __future__ import annotations

import os
import threading
import time
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import QApplication

from whisper_dictate.application import (
    SKRIVI_ICON_SIZES,
    create_application,
    skrivi_icon,
)
from whisper_dictate.i18n import InterfaceLanguage, set_interface_language
from whisper_dictate.indicator import FloatingIndicator, overlay_position
from whisper_dictate.model_ui import ModelManagerPanel
from whisper_dictate.models import LocalModelManager, ModelState, ModelStatus
from whisper_dictate.settings import LanguageMode, SettingsStore, UserSettings
from whisper_dictate.settings_window import (
    HotkeyCaptureButton,
    SettingsWindow,
    hotkey_from_qt_key,
)
from whisper_dictate.tray import TrayIcon


@pytest.fixture(autouse=True)
def reset_interface_language():
    set_interface_language(InterfaceLanguage.ENGLISH)
    yield
    set_interface_language(InterfaceLanguage.ENGLISH)


def application() -> QApplication:
    return create_application("Skrivi tests")


def process_events_until(predicate, timeout: float = 1.0) -> None:
    deadline = time.monotonic() + timeout
    app = application()
    while time.monotonic() < deadline and not predicate():
        app.processEvents()
        time.sleep(0.005)


def test_tray_icon_has_native_small_sizes_and_uses_the_available_canvas() -> None:
    application()
    icon = skrivi_icon()

    assert {(size.width(), size.height()) for size in icon.availableSizes()} == {
        (size, size) for size in SKRIVI_ICON_SIZES
    }

    image = icon.pixmap(16, 16).toImage()
    visible = [
        (x, y)
        for y in range(image.height())
        for x in range(image.width())
        if image.pixelColor(x, y).alpha() > 0
    ]
    assert min(x for x, _ in visible) <= 1
    assert max(x for x, _ in visible) >= 14
    assert min(y for _, y in visible) <= 1
    assert max(y for _, y in visible) >= 14


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
    assert indicator.accessibleName() == "Skrivi dictation status"


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


def test_settings_window_saves_interface_language_choice(tmp_path: Path) -> None:
    application()
    store = SettingsStore(tmp_path / "settings.json")
    window = SettingsWindow(store)

    window.interface_language_combo.setCurrentIndex(
        window.interface_language_combo.findData(
            InterfaceLanguage.NORWEGIAN_BOKMAL.value
        )
    )
    window._save()

    assert (
        store.load().settings.interface_language is InterfaceLanguage.NORWEGIAN_BOKMAL
    )


def test_hotkey_capture_translation_accepts_only_safe_keys() -> None:
    assert hotkey_from_qt_key(int(Qt.Key.Key_Control), 0xA3) == "right_ctrl"
    assert hotkey_from_qt_key(int(Qt.Key.Key_Alt), 0xA5) is None
    assert hotkey_from_qt_key(int(Qt.Key.Key_Control), 0x11, 0xE01D) == ("right_ctrl")
    assert hotkey_from_qt_key(int(Qt.Key.Key_Alt), 0x12, 0xE038) is None
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

    assert window.accessibleName() == "Skrivi settings"
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


def test_model_download_progress_is_specific_and_cancellable(tmp_path: Path) -> None:
    application()
    manager = LocalModelManager(tmp_path / "models")
    runtime = type("Runtime", (), {"active_model": "small"})()
    panel = ModelManagerPanel(manager, runtime, memory_gb=8.0)

    panel._status_changed(
        ModelStatus(
            "base",
            ModelState.DOWNLOADING,
            0.25,
            "Downloading Base…",
            37_000_000,
            148_000_000,
        )
    )

    assert panel.selected_identifier() == "base"
    assert panel.progress.value() == 25
    assert panel.progress.format() == "Downloading Base: 37 MB of 148 MB (25%)"
    assert panel.cancel_button.isHidden() is False
    assert panel.cancel_button.isEnabled() is True
    assert panel.cancel_button.accessibleName() == "Cancel model download"


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


def test_tray_offers_model_retry_only_after_model_load_failure() -> None:
    application()
    events: list[str] = []
    tray = TrayIcon(
        lambda: None,
        on_settings=lambda: None,
        on_retry_model=lambda: events.append("retry"),
    )

    assert tray.retry_model_action.isVisible() is False

    tray.set_status("model_error", "Speech model unavailable")

    assert tray.retry_model_action.isVisible() is True
    assert tray.retry_model_action.text().replace("&", "") == "Retry speech model"
    tray.retry_model_action.trigger()
    assert events == ["retry"]

    tray.set_status("ready", "Ready")
    assert tray.retry_model_action.isVisible() is False


def test_norwegian_interface_covers_settings_models_tray_and_overlay(
    tmp_path: Path,
) -> None:
    application()
    store = SettingsStore(tmp_path / "settings.json")
    store.save(UserSettings(interface_language=InterfaceLanguage.NORWEGIAN_BOKMAL))
    try:
        window = SettingsWindow(store)
        tray = TrayIcon(lambda: None, on_settings=lambda: None)
        indicator = FloatingIndicator(enabled=False)
        statuses: list[str] = []
        indicator.status_changed.connect(lambda _state, text: statuses.append(text))

        indicator.post("transcribing")
        process_events_until(lambda: bool(statuses))

        assert window.windowTitle() == "Innstillinger for Skrivi"
        assert window.accessibleName() == "Skrivi-innstillinger"
        assert [window.tabs.tabText(index).replace("&", "") for index in range(4)] == [
            "Generelt",
            "Modeller",
            "Personvern",
            "Om Skrivi",
        ]
        assert window.model_panel.download_button.text().replace("&", "") == (
            "Last ned"
        )
        assert window.language_combo.itemText(1) == "English"
        assert window.interface_language_combo.itemText(1) == "English"
        assert window.interface_language_combo.itemText(2) == "Norsk bokmål"
        assert tray.settings_action.text().replace("&", "") == "Innstillinger…"
        assert tray.exit_action.text().replace("&", "") == "Avslutt"
        assert statuses == ["Transkriberer lokalt …"]
    finally:
        set_interface_language(InterfaceLanguage.ENGLISH)


def test_interface_language_previews_live_cancel_restores_and_save_persists(
    tmp_path: Path,
) -> None:
    application()
    set_interface_language(InterfaceLanguage.ENGLISH)
    store = SettingsStore(tmp_path / "settings.json")
    store.save(UserSettings(interface_language=InterfaceLanguage.ENGLISH))
    indicator = FloatingIndicator(enabled=False)
    window = SettingsWindow(store)
    tray = TrayIcon(lambda: None, on_settings=lambda: None)
    indicator.status_changed.connect(tray.set_status)
    indicator.status_changed.connect(window.set_status)
    indicator.post("ready")
    process_events_until(lambda: window._status.text().startswith("Ready"))

    norwegian_index = window.interface_language_combo.findData(
        InterfaceLanguage.NORWEGIAN_BOKMAL.value
    )
    window.interface_language_combo.setCurrentIndex(norwegian_index)

    assert window.windowTitle() == "Innstillinger for Skrivi"
    assert window._status.text() == "Klar. Hold Høyre Ctrl for å diktere"
    assert window.model_panel.download_button.text().replace("&", "") == "Last ned"
    assert tray.settings_action.text().replace("&", "") == "Innstillinger…"
    assert store.load().settings.interface_language is InterfaceLanguage.ENGLISH

    window.reject()

    assert window.windowTitle() == "Skrivi Settings"
    assert window._status.text() == "Ready. Hold Right Ctrl to dictate"
    assert window.model_panel.download_button.text().replace("&", "") == "Download"
    assert tray.settings_action.text().replace("&", "") == "Settings…"
    assert store.load().settings.interface_language is InterfaceLanguage.ENGLISH

    window.reload()
    window.interface_language_combo.setCurrentIndex(norwegian_index)
    window._save()

    assert (
        store.load().settings.interface_language is InterfaceLanguage.NORWEGIAN_BOKMAL
    )
    assert window.windowTitle() == "Innstillinger for Skrivi"
    set_interface_language(InterfaceLanguage.ENGLISH)


def test_model_download_progress_retranslates_while_active(tmp_path: Path) -> None:
    application()
    set_interface_language(InterfaceLanguage.ENGLISH)
    manager = LocalModelManager(tmp_path / "models")
    runtime = type("Runtime", (), {"active_model": "small"})()
    panel = ModelManagerPanel(manager, runtime, memory_gb=8.0)
    status = ModelStatus(
        "base",
        ModelState.DOWNLOADING,
        0.25,
        "Downloading Base…",
        37_000_000,
        148_000_000,
    )
    panel._status_changed(status)

    set_interface_language(InterfaceLanguage.NORWEGIAN_BOKMAL)
    panel.retranslate_ui()

    assert panel.state.text() == "Laster ned Base …"
    assert panel.progress.format() == "Laster ned Base: 37 MB av 148 MB (25 %)"
    assert panel.cancel_button.text().replace("&", "") == "Avbryt nedlasting"
    set_interface_language(InterfaceLanguage.ENGLISH)
