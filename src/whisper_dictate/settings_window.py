from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import QSignalBlocker, Qt, Signal, Slot
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
from whisper_dictate.i18n import (
    InterfaceLanguage,
    add_interface_language_listener,
    set_interface_language,
    tr,
)
from whisper_dictate.model_runtime import ModelRuntime
from whisper_dictate.model_ui import ModelManagerPanel
from whisper_dictate.models import LocalModelManager
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

INTERFACE_LANGUAGE_CHOICES = (
    ("Automatic (Windows display language)", InterfaceLanguage.AUTOMATIC),
    ("English", InterfaceLanguage.ENGLISH),
    ("Norwegian Bokmål", InterfaceLanguage.NORWEGIAN_BOKMAL),
)


def hotkey_from_qt_key(
    key: int, native_virtual_key: int, native_scan_code: int = 0
) -> str | None:
    """Translate a captured Windows key into a supported Skrivi identifier."""
    # Qt normally receives the generic VK_CONTROL/VK_MENU values from Windows.
    # Right-side modifier keys are distinguished by their extended scan codes.
    # Accept the side-specific virtual keys too, because synthetic events and
    # some keyboard drivers provide those instead.
    if native_virtual_key == 0xA3 or (
        key == int(Qt.Key.Key_Control) and native_scan_code in {0xE01D, 0x11D}
    ):
        return "right_ctrl"
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
        super().__init__(f"&{tr('Change…')}", parent)
        self._capturing = False
        self._captured_identifier: str | None = None
        self._can_capture = can_capture or (lambda: True)
        self.setAccessibleName(tr("Change push-to-talk key"))
        self.setAccessibleDescription(
            tr("Press this button, then press Right Ctrl or F6 through F12.")
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
                tr("Finish the current recording before changing the push-to-talk key.")
            )
            return
        self._capturing = True
        self._captured_identifier = None
        self.setText(tr("Press a key…"))
        self.setAccessibleName(tr("Waiting for a push-to-talk key"))
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
        self._captured_identifier = None
        self.setText(f"&{tr('Change…')}")
        self.setAccessibleName(tr("Change push-to-talk key"))
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
        identifier = hotkey_from_qt_key(
            event.key(), event.nativeVirtualKey(), event.nativeScanCode()
        )
        if identifier is None:
            self.capture_rejected.emit(
                tr(
                    "Use Right Ctrl or F6 through F12. Letters, Windows "
                    "keys, and common editing keys are not safe choices."
                )
            )
            event.accept()
            return
        self._captured_identifier = identifier
        self.hotkey_captured.emit(identifier)
        self.setText(tr("Release key…"))
        self.setAccessibleName(tr("Release the selected push-to-talk key"))
        event.accept()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if not self._capturing or self._captured_identifier is None:
            super().keyReleaseEvent(event)
            return
        if event.isAutoRepeat():
            event.accept()
            return
        identifier = hotkey_from_qt_key(
            event.key(), event.nativeVirtualKey(), event.nativeScanCode()
        )
        if identifier == self._captured_identifier:
            # Keep the global listener stopped until the selected key is
            # physically up. Restarting it on key-down can give pynput half of
            # the capture event and leave push-to-talk permanently pressed.
            self._finish_capture()
        event.accept()

    def retranslate_ui(self) -> None:
        self.setAccessibleDescription(
            tr("Press this button, then press Right Ctrl or F6 through F12.")
        )
        if not self._capturing:
            self.setText(f"&{tr('Change…')}")
            self.setAccessibleName(tr("Change push-to-talk key"))
        elif self._captured_identifier is None:
            self.setText(tr("Press a key…"))
            self.setAccessibleName(tr("Waiting for a push-to-talk key"))
        else:
            self.setText(tr("Release key…"))
            self.setAccessibleName(tr("Release the selected push-to-talk key"))


class SettingsWindow(QDialog):
    """Keyboard-operable settings that can update a running Skrivi instance."""

    settings_saved = Signal(object)
    hotkey_capture_started = Signal()
    hotkey_capture_finished = Signal()

    def __init__(
        self,
        store: SettingsStore,
        *,
        title: str = "Skrivi",
        save_settings: Callable[[UserSettings], None] | None = None,
        microphone_provider: Callable[[], list[MicrophoneDevice]] | None = None,
        can_change_input: Callable[[], bool] | None = None,
        active_model: str = "small",
        model_manager: LocalModelManager | None = None,
        model_runtime: ModelRuntime | None = None,
    ) -> None:
        super().__init__()
        self._store = store
        self._save_settings = save_settings or store.save
        self._microphone_provider = microphone_provider or self._default_microphones
        self._can_change_input = can_change_input or (lambda: True)
        self._title = title
        self._active_model = active_model
        self._model_runtime = model_runtime
        self._settings = UserSettings()
        self._settings_warning: str | None = None
        self._status_state = "starting"
        self._selected_hotkey = DEFAULT_HOTKEY
        self.setWindowTitle(tr("{title} Settings", title=title))
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setMinimumSize(600, 560)
        self.setAccessibleName(tr("Skrivi settings"))
        self.setAccessibleDescription(
            tr("Configure Skrivi and review its local privacy behaviour.")
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(14)

        self._heading = QLabel(tr("Skrivi settings"), self)
        self._heading.setAccessibleName(tr("Skrivi settings heading"))
        heading_font = self._heading.font()
        heading_font.setBold(True)
        heading_font.setPointSize(max(heading_font.pointSize() + 5, 16))
        self._heading.setFont(heading_font)
        root.addWidget(self._heading)

        self._warning = QLabel(self)
        self._warning.setWordWrap(True)
        self._warning.setAccessibleName(tr("Settings warning"))
        self._warning.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        root.addWidget(self._warning)

        self.tabs = QTabWidget(self)
        self.tabs.setAccessibleName(tr("Settings sections"))
        self.tabs.addTab(self._general_page(), f"&{tr('General')}")
        self.model_panel = ModelManagerPanel(model_manager, model_runtime, self)
        self.model_panel.model_activated.connect(self._model_activated)
        self.tabs.addTab(self.model_panel, f"&{tr('Models')}")
        self.tabs.addTab(self._privacy_page(), f"&{tr('Privacy')}")
        self.tabs.addTab(self._about_page(), f"&{tr('About')}")
        root.addWidget(self.tabs, 1)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        self.buttons.setAccessibleName(tr("Settings actions"))
        self.buttons.accepted.connect(self._save)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

        save_button = self.buttons.button(QDialogButtonBox.StandardButton.Save)
        if save_button is not None:
            save_button.setText(f"&{tr('Save')}")
            save_button.setAccessibleName(tr("Save settings"))
        cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button is not None:
            cancel_button.setText(f"&{tr('Cancel')}")
            cancel_button.setAccessibleName(tr("Cancel changes"))

        self.save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        self.save_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self.save_shortcut.activated.connect(self._save)
        self.interface_language_combo.currentIndexChanged.connect(
            self._preview_interface_language
        )
        add_interface_language_listener(self.retranslate_ui)
        self.reload()

    @staticmethod
    def _default_microphones() -> list[MicrophoneDevice]:
        return [
            MicrophoneDevice(
                WINDOWS_DEFAULT_MICROPHONE, tr("Windows Default"), "Windows", None
            )
        ]

    def _general_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(16)

        self._status_group = QGroupBox(tr("Current status"), page)
        status_layout = QVBoxLayout(self._status_group)
        self._status = QLabel(tr("Starting"), self._status_group)
        self._status.setWordWrap(True)
        self._status.setAccessibleName(tr("Current dictation status"))
        status_layout.addWidget(self._status)
        layout.addWidget(self._status_group)

        self._setup_group = QGroupBox(tr("Dictation setup"), page)
        setup_layout = QFormLayout(self._setup_group)

        self.language_combo = QComboBox(self._setup_group)
        self.language_combo.setAccessibleName(tr("Dictation language"))
        for label, mode in LANGUAGE_CHOICES:
            self.language_combo.addItem(tr(label), mode.value)
        self._language_label = QLabel(f"&{tr('Language')}:", self._setup_group)
        self._language_label.setBuddy(self.language_combo)
        setup_layout.addRow(self._language_label, self.language_combo)
        self._language_help = QLabel(
            tr(
                "Automatic detects one language per recording and works best with a "
                "complete phrase. Multilingual can detect language again within a "
                "recording."
            ),
            self._setup_group,
        )
        self._language_help.setWordWrap(True)
        setup_layout.addRow(self._language_help)

        self._model = self._value_label(tr("Speech model value"))
        self._model_label = QLabel(f"{tr('Speech model')}:", self._setup_group)
        setup_layout.addRow(self._model_label, self._model)

        self.interface_language_combo = QComboBox(self._setup_group)
        self.interface_language_combo.setAccessibleName(tr("Interface language"))
        for label, language in INTERFACE_LANGUAGE_CHOICES:
            self.interface_language_combo.addItem(tr(label), language.value)
        self._interface_language_label = QLabel(
            f"{tr('Interface language')}:", self._setup_group
        )
        self._interface_language_label.setBuddy(self.interface_language_combo)
        setup_layout.addRow(
            self._interface_language_label, self.interface_language_combo
        )
        self._interface_help = QLabel(
            tr("Interface language updates immediately."), self._setup_group
        )
        self._interface_help.setWordWrap(True)
        setup_layout.addRow(self._interface_help)

        microphone_row = QWidget(self._setup_group)
        microphone_layout = QHBoxLayout(microphone_row)
        microphone_layout.setContentsMargins(0, 0, 0, 0)
        self.microphone_combo = QComboBox(microphone_row)
        self.microphone_combo.setAccessibleName(tr("Microphone"))
        self.refresh_microphones_button = QPushButton(
            f"&{tr('Refresh')}", microphone_row
        )
        self.refresh_microphones_button.setAccessibleName(tr("Refresh microphones"))
        self.refresh_microphones_button.clicked.connect(self._refresh_microphones)
        microphone_layout.addWidget(self.microphone_combo, 1)
        microphone_layout.addWidget(self.refresh_microphones_button)
        self._microphone_label = QLabel(f"&{tr('Microphone')}:", self._setup_group)
        self._microphone_label.setBuddy(self.microphone_combo)
        setup_layout.addRow(self._microphone_label, microphone_row)
        self._microphone_help = QLabel(self._setup_group)
        self._microphone_help.setWordWrap(True)
        self._microphone_help.setAccessibleName(tr("Microphone availability"))
        setup_layout.addRow(self._microphone_help)

        hotkey_row = QWidget(self._setup_group)
        hotkey_layout = QHBoxLayout(hotkey_row)
        hotkey_layout.setContentsMargins(0, 0, 0, 0)
        self._hotkey = self._value_label(tr("Push-to-talk key value"))
        self.hotkey_capture_button = HotkeyCaptureButton(
            hotkey_row, can_capture=self._can_change_input
        )
        self.restore_hotkey_button = QPushButton(
            f"&{tr('Restore Default')}", hotkey_row
        )
        self.restore_hotkey_button.setAccessibleName(
            tr("Restore default push-to-talk key")
        )
        hotkey_layout.addWidget(self._hotkey, 1)
        hotkey_layout.addWidget(self.hotkey_capture_button)
        hotkey_layout.addWidget(self.restore_hotkey_button)
        self._hotkey_label = QLabel(f"{tr('Push-to-talk key')}:", self._setup_group)
        setup_layout.addRow(self._hotkey_label, hotkey_row)
        self._hotkey_help = QLabel(
            tr(
                "Safe choices are Right Ctrl and F6 through F12. "
                "Press Escape to cancel key capture."
            ),
            self._setup_group,
        )
        self._hotkey_help.setWordWrap(True)
        self._hotkey_help.setAccessibleName(tr("Push-to-talk key guidance"))
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
        layout.addWidget(self._setup_group)

        self._appearance_group = QGroupBox(tr("Appearance"), page)
        appearance_layout = QVBoxLayout(self._appearance_group)
        self.overlay_checkbox = QCheckBox(
            f"&{tr('Show the compact status overlay while dictating')}",
            self._appearance_group,
        )
        self.overlay_checkbox.setAccessibleName(tr("Show dictation status overlay"))
        self.overlay_checkbox.setAccessibleDescription(
            tr(
                "Show a non-activating message while Skrivi loads, listens and "
                "transcribes."
            )
        )
        appearance_layout.addWidget(self.overlay_checkbox)
        layout.addWidget(self._appearance_group)
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
        self._privacy = QLabel(
            tr(
                "Speech is processed locally on this PC. Skrivi does not save your "
                "recordings or transcripts, does not use the clipboard for dictated "
                "text, and needs no account. After the selected speech model has been "
                "downloaded, normal dictation does not require internet access."
            ),
            page,
        )
        self._privacy.setWordWrap(True)
        self._privacy.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self._privacy.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self._privacy.setAccessibleName(tr("Skrivi privacy summary"))
        layout.addWidget(self._privacy)
        layout.addStretch(1)
        return page

    def _about_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        self._about = QLabel(
            tr(
                "Skrivi is free and open-source local speech-to-text software.\n\n"
                "The interface uses PySide6 and Qt under their open-source licences. "
                "See THIRD_PARTY_NOTICES.md included with Skrivi for copyright and "
                "licence information."
            ),
            page,
        )
        self._about.setWordWrap(True)
        self._about.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self._about.setAccessibleName(tr("About Skrivi"))
        layout.addWidget(self._about)
        layout.addStretch(1)
        return page

    def _set_hotkey(self, identifier: str) -> None:
        try:
            self._selected_hotkey = validate_hotkey(identifier)
        except HotkeyValidationError as error:
            self._hotkey_help.setText(str(error))
            return
        self._hotkey.setText(tr(hotkey_display_name(self._selected_hotkey)))
        self._hotkey_help.setText(
            tr(
                "Safe choices are Right Ctrl and F6 through F12. "
                "Press Escape to cancel key capture."
            )
        )

    def _select_language(self, language: LanguageMode) -> None:
        index = self.language_combo.findData(language.value)
        self.language_combo.setCurrentIndex(max(index, 0))

    @staticmethod
    def _replace_choices(combo: QComboBox, choices) -> None:
        selected = combo.currentData()
        blocker = QSignalBlocker(combo)
        combo.clear()
        for label, value in choices:
            combo.addItem(tr(label), value.value)
        index = combo.findData(selected)
        combo.setCurrentIndex(max(index, 0))
        del blocker

    @Slot(int)
    def _preview_interface_language(self, index: int) -> None:
        if index < 0:
            return
        set_interface_language(
            InterfaceLanguage(self.interface_language_combo.itemData(index))
        )

    def retranslate_ui(self) -> None:
        self.setWindowTitle(tr("{title} Settings", title=self._title))
        self.setAccessibleName(tr("Skrivi settings"))
        self.setAccessibleDescription(
            tr("Configure Skrivi and review its local privacy behaviour.")
        )
        self._heading.setText(tr("Skrivi settings"))
        self._heading.setAccessibleName(tr("Skrivi settings heading"))
        self._warning.setAccessibleName(tr("Settings warning"))
        self._warning.setText(
            tr(self._settings_warning) if self._settings_warning else ""
        )
        self.tabs.setAccessibleName(tr("Settings sections"))
        self.tabs.setTabText(0, f"&{tr('General')}")
        self.tabs.setTabText(1, f"&{tr('Models')}")
        self.tabs.setTabText(2, f"&{tr('Privacy')}")
        self.tabs.setTabText(3, f"&{tr('About')}")
        self.buttons.setAccessibleName(tr("Settings actions"))
        save_button = self.buttons.button(QDialogButtonBox.StandardButton.Save)
        if save_button is not None:
            save_button.setText(f"&{tr('Save')}")
            save_button.setAccessibleName(tr("Save settings"))
        cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button is not None:
            cancel_button.setText(f"&{tr('Cancel')}")
            cancel_button.setAccessibleName(tr("Cancel changes"))

        self._status_group.setTitle(tr("Current status"))
        if self._status_state == "starting":
            self._status.setText(tr("Starting"))
        self._status.setAccessibleName(tr("Current dictation status"))
        self._setup_group.setTitle(tr("Dictation setup"))
        self._replace_choices(self.language_combo, LANGUAGE_CHOICES)
        self.language_combo.setAccessibleName(tr("Dictation language"))
        self._language_label.setText(f"&{tr('Language')}:")
        self._language_help.setText(
            tr(
                "Automatic detects one language per recording and works best with a "
                "complete phrase. Multilingual can detect language again within a "
                "recording."
            )
        )
        self._model_label.setText(f"{tr('Speech model')}:")
        self._model.setAccessibleName(tr("Speech model value"))
        self._replace_choices(self.interface_language_combo, INTERFACE_LANGUAGE_CHOICES)
        self.interface_language_combo.setAccessibleName(tr("Interface language"))
        self._interface_language_label.setText(f"{tr('Interface language')}:")
        self._interface_help.setText(tr("Interface language updates immediately."))
        self.microphone_combo.setAccessibleName(tr("Microphone"))
        self.refresh_microphones_button.setText(f"&{tr('Refresh')}")
        self.refresh_microphones_button.setAccessibleName(tr("Refresh microphones"))
        self._microphone_label.setText(f"&{tr('Microphone')}:")
        self._microphone_help.setAccessibleName(tr("Microphone availability"))
        self._hotkey_label.setText(f"{tr('Push-to-talk key')}:")
        self._hotkey.setAccessibleName(tr("Push-to-talk key value"))
        self.hotkey_capture_button.retranslate_ui()
        self.restore_hotkey_button.setText(f"&{tr('Restore Default')}")
        self.restore_hotkey_button.setAccessibleName(
            tr("Restore default push-to-talk key")
        )
        self._set_hotkey(self._selected_hotkey)
        self._hotkey_help.setAccessibleName(tr("Push-to-talk key guidance"))
        self._appearance_group.setTitle(tr("Appearance"))
        self.overlay_checkbox.setText(
            f"&{tr('Show the compact status overlay while dictating')}"
        )
        self.overlay_checkbox.setAccessibleName(tr("Show dictation status overlay"))
        self.overlay_checkbox.setAccessibleDescription(
            tr(
                "Show a non-activating message while Skrivi loads, listens and "
                "transcribes."
            )
        )
        self._privacy.setText(
            tr(
                "Speech is processed locally on this PC. Skrivi does not save your "
                "recordings or transcripts, does not use the clipboard for dictated "
                "text, and needs no account. After the selected speech model has been "
                "downloaded, normal dictation does not require internet access."
            )
        )
        self._privacy.setAccessibleName(tr("Skrivi privacy summary"))
        self._about.setText(
            tr(
                "Skrivi is free and open-source local speech-to-text software.\n\n"
                "The interface uses PySide6 and Qt under their open-source licences. "
                "See THIRD_PARTY_NOTICES.md included with Skrivi for copyright and "
                "licence information."
            )
        )
        self._about.setAccessibleName(tr("About Skrivi"))
        self._refresh_microphones()
        self.model_panel.retranslate_ui()

    @Slot()
    def _refresh_microphones(self) -> None:
        selected = self.microphone_combo.currentData() or self._settings.microphone
        try:
            devices = self._microphone_provider()
            warning = ""
        except Exception:
            devices = self._default_microphones()
            warning = tr(
                "Microphones could not be listed. Check Windows Sound settings "
                "or use Windows Default."
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
            self.microphone_combo.addItem(
                tr("Unavailable: {name}", name=name), selected
            )
            selected_index = self.microphone_combo.count() - 1
            warning = tr(
                "The saved microphone is disconnected. Choose another microphone "
                "or Windows Default before saving."
            )
        self.microphone_combo.setCurrentIndex(max(selected_index, 0))
        self._microphone_help.setText(warning)
        self._microphone_help.setVisible(bool(warning))

    def reload(self) -> SettingsLoadResult:
        result = self._store.load()
        self._settings = result.settings
        self._settings_warning = result.warning
        set_interface_language(self._settings.interface_language)
        self._warning.setText(tr(result.warning) if result.warning else "")
        self._warning.setVisible(result.warning is not None)
        self.overlay_checkbox.setChecked(self._settings.overlay_enabled)
        self._select_language(self._settings.language)
        blocker = QSignalBlocker(self.interface_language_combo)
        interface_index = self.interface_language_combo.findData(
            self._settings.interface_language.value
        )
        self.interface_language_combo.setCurrentIndex(max(interface_index, 0))
        del blocker
        active_model = (
            self._model_runtime.active_model
            if self._model_runtime is not None
            else self._active_model
        )
        self._model.setText(active_model)
        self.model_panel.select_model(active_model)
        self.model_panel.refresh()
        self._set_hotkey(self._settings.hotkey)
        self._refresh_microphones()
        return result

    @Slot(str)
    def _model_activated(self, identifier: str) -> None:
        self._active_model = identifier
        self._model.setText(identifier)
        self._settings = self._store.load().settings

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
        self._status_state = state
        self._status.setText(text)

    @Slot()
    def reject(self) -> None:
        self.hotkey_capture_button.cancel_capture()
        set_interface_language(self._settings.interface_language)
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
            interface_language=InterfaceLanguage(
                self.interface_language_combo.currentData()
            ),
        )
        try:
            self._save_settings(updated)
        except (SettingsWriteError, RuntimeSettingsError) as error:
            QMessageBox.critical(
                self,
                tr("Settings could not be applied"),
                tr(str(error))
                or tr(
                    "Skrivi could not apply settings safely. Previous settings "
                    "remain active."
                ),
            )
            return
        self._settings = updated
        self.settings_saved.emit(updated)
        self.accept()
