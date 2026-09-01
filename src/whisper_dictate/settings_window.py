from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QKeyEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from whisper_dictate.audio import (
    WINDOWS_DEFAULT_MICROPHONE,
    MicrophoneDevice,
    microphone_name_from_identifier,
)
from whisper_dictate.hotkeys import (
    DEFAULT_HOTKEY,
    HotkeyValidationError,
    hotkey_display_name,
    validate_hotkey,
)
from whisper_dictate.runtime_settings import RuntimeSettingsError
from whisper_dictate.settings import (
    LanguageMode,
    SettingsLoadResult,
    SettingsStore,
    SettingsWriteError,
    UserSettings,
)

LANGUAGE_CHOICES = (
    ("Automatic", LanguageMode.AUTOMATIC),
    ("English", LanguageMode.ENGLISH),
    ("Norwegian", LanguageMode.NORWEGIAN),
    ("Multilingual", LanguageMode.MULTILINGUAL),
)


def hotkey_from_qt_key(key: int, native_virtual_key: int) -> str | None:
    """Translate a captured Windows key into a supported Bragi identifier."""
    if native_virtual_key == 0xA3:
        return "right_ctrl"
    if native_virtual_key == 0xA5:
        return "right_alt"
    function_keys = {
        int(getattr(Qt.Key, f"Key_F{number}")): f"f{number}" for number in range(6, 13)
    }
    return function_keys.get(key)


class HotkeyCaptureButton(QPushButton):
    capture_started = Signal()
    capture_finished = Signal()
    hotkey_captured = Signal(str)
    capture_rejected = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        can_capture: Callable[[], bool] | None = None,
    ) -> None:
        super().__init__("&Change…", parent)
        self._capturing = False
        self._can_capture = can_capture or (lambda: True)
        self.setAccessibleName("Change push-to-talk key")
        self.setAccessibleDescription(
            "Press this button, then press Right Ctrl, Right Alt, or F6 through F12."
        )
        self.clicked.connect(self.begin_capture)

    @property
    def is_capturing(self) -> bool:
        return self._capturing

    @Slot()
    def begin_capture(self) -> None:
        if self._capturing:
            return
        if not self._can_capture():
            self.capture_rejected.emit(
                "Finish the current recording before changing the push-to-talk key."
            )
            return
        self._capturing = True
        self.setText("Press a key…")
        self.setAccessibleName("Waiting for a push-to-talk key")
        self.grabKeyboard()
        self.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.capture_started.emit()

    @Slot()
    def cancel_capture(self) -> None:
        if self._capturing:
            self._finish_capture()

    def _finish_capture(self) -> None:
        self.releaseKeyboard()
        self._capturing = False
        self.setText("&Change…")
        self.setAccessibleName("Change push-to-talk key")
        self.capture_finished.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if not self._capturing:
            super().keyPressEvent(event)
            return
        if event.isAutoRepeat():
            event.accept()
            return
        if event.key() == int(Qt.Key.Key_Escape):
            self._finish_capture()
            event.accept()
            return
        identifier = hotkey_from_qt_key(event.key(), event.nativeVirtualKey())
        if identifier is None:
            self.capture_rejected.emit(
                "Use Right Ctrl, Right Alt, or F6 through F12. Letters, Windows "
                "keys, and common editing keys are not safe choices."
            )
            event.accept()
            return
        self.hotkey_captured.emit(identifier)
        self._finish_capture()
        event.accept()


class SettingsWindow(QDialog):
    """Keyboard-operable settings that can update a running Bragi instance."""

    settings_saved = Signal(object)
    hotkey_capture_started = Signal()
    hotkey_capture_finished = Signal()

    def __init__(
        self,
        store: SettingsStore,
        *,
        title: str = "Bragi",
        save_settings: Callable[[UserSettings], None] | None = None,
        microphone_provider: Callable[[], list[MicrophoneDevice]] | None = None,
        can_change_input: Callable[[], bool] | None = None,
        active_model: str = "small",
    ) -> None:
        super().__init__()
        self._store = store
        self._save_settings = save_settings or store.save
        self._microphone_provider = microphone_provider or self._default_microphones
        self._can_change_input = can_change_input or (lambda: True)
        self._active_model = active_model
        self._settings = UserSettings()
        self._selected_hotkey = DEFAULT_HOTKEY
        self.setWindowTitle(f"{title} Settings")
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setMinimumSize(600, 560)
        self.setAccessibleName("Bragi settings")
        self.setAccessibleDescription(
            "Configure Bragi and review its local privacy behaviour."
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(14)

        heading = QLabel("Bragi settings", self)
        heading.setAccessibleName("Bragi settings heading")
        heading_font = heading.font()
        heading_font.setBold(True)
        heading_font.setPointSize(max(heading_font.pointSize() + 5, 16))
        heading.setFont(heading_font)
        root.addWidget(heading)

        self._warning = QLabel(self)
        self._warning.setWordWrap(True)
        self._warning.setAccessibleName("Settings warning")
        self._warning.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        root.addWidget(self._warning)

        self.tabs = QTabWidget(self)
        self.tabs.setAccessibleName("Settings sections")
        self.tabs.addTab(self._general_page(), "&General")
        self.tabs.addTab(self._privacy_page(), "&Privacy")
        self.tabs.addTab(self._about_page(), "&About")
        root.addWidget(self.tabs, 1)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        self.buttons.setAccessibleName("Settings actions")
        self.buttons.accepted.connect(self._save)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

        save_button = self.buttons.button(QDialogButtonBox.StandardButton.Save)
        if save_button is not None:
            save_button.setText("&Save")
            save_button.setAccessibleName("Save settings")
        cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button is not None:
            cancel_button.setText("&Cancel")
            cancel_button.setAccessibleName("Cancel changes")

        self.save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        self.save_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self.save_shortcut.activated.connect(self._save)
        self.reload()

    @staticmethod
    def _default_microphones() -> list[MicrophoneDevice]:
        return [
            MicrophoneDevice(
                WINDOWS_DEFAULT_MICROPHONE, "Windows Default", "Windows", None
            )
        ]

    def _general_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(16)

        status_group = QGroupBox("Current status", page)
        status_layout = QVBoxLayout(status_group)
        self._status = QLabel("Starting", status_group)
        self._status.setWordWrap(True)
        self._status.setAccessibleName("Current dictation status")
        status_layout.addWidget(self._status)
        layout.addWidget(status_group)

        setup_group = QGroupBox("Dictation setup", page)
        setup_layout = QFormLayout(setup_group)

        self.language_combo = QComboBox(setup_group)
        self.language_combo.setAccessibleName("Dictation language")
        for label, mode in LANGUAGE_CHOICES:
            self.language_combo.addItem(label, mode.value)
        setup_layout.addRow("&Language:", self.language_combo)
        language_help = QLabel(
            "Automatic detects one language per recording and works best with a "
            "complete phrase. Multilingual can detect language again within a "
            "recording.",
            setup_group,
        )
        language_help.setWordWrap(True)
        setup_layout.addRow(language_help)

        self._model = self._value_label("Speech model value")
        setup_layout.addRow("Speech model:", self._model)

        microphone_row = QWidget(setup_group)
        microphone_layout = QHBoxLayout(microphone_row)
        microphone_layout.setContentsMargins(0, 0, 0, 0)
        self.microphone_combo = QComboBox(microphone_row)
        self.microphone_combo.setAccessibleName("Microphone")
        self.refresh_microphones_button = QPushButton("&Refresh", microphone_row)
        self.refresh_microphones_button.setAccessibleName("Refresh microphones")
        self.refresh_microphones_button.clicked.connect(self._refresh_microphones)
        microphone_layout.addWidget(self.microphone_combo, 1)
        microphone_layout.addWidget(self.refresh_microphones_button)
        setup_layout.addRow("&Microphone:", microphone_row)
        self._microphone_help = QLabel(setup_group)
        self._microphone_help.setWordWrap(True)
        self._microphone_help.setAccessibleName("Microphone availability")
        setup_layout.addRow(self._microphone_help)

        hotkey_row = QWidget(setup_group)
        hotkey_layout = QHBoxLayout(hotkey_row)
        hotkey_layout.setContentsMargins(0, 0, 0, 0)
        self._hotkey = self._value_label("Push-to-talk key value")
        self.hotkey_capture_button = HotkeyCaptureButton(
            hotkey_row, can_capture=self._can_change_input
        )
        self.restore_hotkey_button = QPushButton("Restore &Default", hotkey_row)
        self.restore_hotkey_button.setAccessibleName("Restore default push-to-talk key")
        hotkey_layout.addWidget(self._hotkey, 1)
        hotkey_layout.addWidget(self.hotkey_capture_button)
        hotkey_layout.addWidget(self.restore_hotkey_button)
        setup_layout.addRow("Push-to-talk key:", hotkey_row)
        self._hotkey_help = QLabel(
            "Safe choices are Right Ctrl, Right Alt, and F6 through F12. "
            "Press Escape to cancel key capture.",
            setup_group,
        )
        self._hotkey_help.setWordWrap(True)
        self._hotkey_help.setAccessibleName("Push-to-talk key guidance")
        setup_layout.addRow(self._hotkey_help)
        self.hotkey_capture_button.hotkey_captured.connect(self._set_hotkey)
        self.hotkey_capture_button.capture_rejected.connect(self._hotkey_help.setText)
        self.hotkey_capture_button.capture_started.connect(self.hotkey_capture_started)
        self.hotkey_capture_button.capture_finished.connect(
            self.hotkey_capture_finished
        )
        self.restore_hotkey_button.clicked.connect(
            lambda: self._set_hotkey(DEFAULT_HOTKEY)
        )
        layout.addWidget(setup_group)

        appearance_group = QGroupBox("Appearance", page)
        appearance_layout = QVBoxLayout(appearance_group)
        self.overlay_checkbox = QCheckBox(
            "Show the compact status &overlay while dictating", appearance_group
        )
        self.overlay_checkbox.setAccessibleName("Show dictation status overlay")
        self.overlay_checkbox.setAccessibleDescription(
            "Show a non-activating message while Bragi loads, listens and transcribes."
        )
        appearance_layout.addWidget(self.overlay_checkbox)
        layout.addWidget(appearance_group)
        layout.addStretch(1)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(page)
        return scroll

    @staticmethod
    def _value_label(accessible_name: str) -> QLabel:
        label = QLabel()
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByKeyboard)
        label.setAccessibleName(accessible_name)
        return label

    def _privacy_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        privacy = QLabel(
            "Speech is processed locally on this PC. Bragi does not save your "
            "recordings or transcripts, does not use the clipboard for dictated "
            "text, and needs no account. After the selected speech model has been "
            "downloaded, normal dictation does not require internet access.",
            page,
        )
        privacy.setWordWrap(True)
        privacy.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        privacy.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByKeyboard)
        privacy.setAccessibleName("Bragi privacy summary")
        layout.addWidget(privacy)
        layout.addStretch(1)
        return page

    def _about_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        about = QLabel(
            "Bragi is free and open-source local speech-to-text software.\n\n"
            "The interface uses PySide6 and Qt under their open-source licences. "
            "See THIRD_PARTY_NOTICES.md included with Bragi for copyright and "
            "licence information.",
            page,
        )
        about.setWordWrap(True)
        about.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByKeyboard)
        about.setAccessibleName("About Bragi")
        layout.addWidget(about)
        layout.addStretch(1)
        return page

    def _set_hotkey(self, identifier: str) -> None:
        try:
            self._selected_hotkey = validate_hotkey(identifier)
        except HotkeyValidationError as error:
            self._hotkey_help.setText(str(error))
            return
        self._hotkey.setText(hotkey_display_name(self._selected_hotkey))
        self._hotkey_help.setText(
            "Safe choices are Right Ctrl, Right Alt, and F6 through F12. "
            "Press Escape to cancel key capture."
        )

    def _select_language(self, language: LanguageMode) -> None:
        index = self.language_combo.findData(language.value)
        self.language_combo.setCurrentIndex(max(index, 0))

    @Slot()
    def _refresh_microphones(self) -> None:
        selected = self.microphone_combo.currentData() or self._settings.microphone
        try:
            devices = self._microphone_provider()
            warning = ""
        except Exception:
            devices = self._default_microphones()
            warning = (
                "Microphones could not be listed. Check Windows Sound settings or "
                "use Windows Default."
            )
        if not any(
            device.identifier == WINDOWS_DEFAULT_MICROPHONE for device in devices
        ):
            devices.insert(0, self._default_microphones()[0])

        self.microphone_combo.clear()
        for device in devices:
            self.microphone_combo.addItem(device.label, device.identifier)
        selected_index = self.microphone_combo.findData(selected)
        if selected_index < 0 and selected != WINDOWS_DEFAULT_MICROPHONE:
            name = microphone_name_from_identifier(str(selected))
            self.microphone_combo.addItem(f"Unavailable: {name}", selected)
            selected_index = self.microphone_combo.count() - 1
            warning = (
                "The saved microphone is disconnected. Choose another microphone "
                "or Windows Default before saving."
            )
        self.microphone_combo.setCurrentIndex(max(selected_index, 0))
        self._microphone_help.setText(warning)
        self._microphone_help.setVisible(bool(warning))

    def reload(self) -> SettingsLoadResult:
        result = self._store.load()
        self._settings = result.settings
        self._warning.setText(result.warning or "")
        self._warning.setVisible(result.warning is not None)
        self.overlay_checkbox.setChecked(self._settings.overlay_enabled)
        self._select_language(self._settings.language)
        self._model.setText(self._active_model)
        self._set_hotkey(self._settings.hotkey)
        self._refresh_microphones()
        return result

    @Slot()
    def show_settings(self) -> None:
        self.reload()
        self.show()
        self.raise_()
        self.activateWindow()
        self.tabs.setCurrentIndex(0)
        self.language_combo.setFocus(Qt.FocusReason.ShortcutFocusReason)

    @Slot(str, str)
    def set_status(self, state: str, text: str) -> None:
        del state
        self._status.setText(text)

    @Slot()
    def reject(self) -> None:
        self.hotkey_capture_button.cancel_capture()
        super().reject()

    @Slot()
    def _save(self) -> None:
        language = LanguageMode(self.language_combo.currentData())
        microphone = self.microphone_combo.currentData()
        updated = replace(
            self._settings,
            language=language,
            hotkey=self._selected_hotkey,
            microphone=microphone,
            overlay_enabled=self.overlay_checkbox.isChecked(),
        )
        try:
            self._save_settings(updated)
        except (SettingsWriteError, RuntimeSettingsError) as error:
            QMessageBox.critical(
                self,
                "Settings could not be applied",
                str(error)
                or "Bragi could not apply settings safely. Previous settings "
                "remain active.",
            )
            return
        self._settings = updated
        self.settings_saved.emit(updated)
        self.accept()
