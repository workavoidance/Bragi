from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import QSignalBlocker, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QKeyEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
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
    HOTKEY_PARTS,
    HotkeyValidationError,
    hotkey_display_name,
    hotkey_identifier_for_parts,
    is_hotkey_part_prefix,
    validate_hotkey,
)
from whisper_dictate.i18n import (
    InterfaceLanguage,
    add_interface_language_listener,
    current_interface_language,
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
    ("Norwegian", LanguageMode.NORWEGIAN),
    ("English", LanguageMode.ENGLISH),
)

INTERFACE_LANGUAGE_CHOICES = (
    ("Automatic (Windows display language)", InterfaceLanguage.AUTOMATIC),
    ("English", InterfaceLanguage.ENGLISH),
    ("Norwegian Bokmål", InterfaceLanguage.NORWEGIAN_BOKMAL),
)

PRIVACY_URL = "https://github.com/workavoidance/Skrivi/blob/main/docs/PRIVACY.md"
PRIVACY_URL_NB = "https://github.com/workavoidance/Skrivi/blob/main/docs/PRIVACY_NB.md"
SOURCE_URL = "https://github.com/workavoidance/Skrivi"
WEBSITE_URL = "https://skrivi.no/"
NOTICES_URL = "https://github.com/workavoidance/Skrivi/blob/main/THIRD_PARTY_NOTICES.md"


def _set_ui_role(widget: QWidget, role: str) -> QWidget:
    widget.setProperty("uiRole", role)
    return widget


def _text_label(
    text: str = "",
    parent: QWidget | None = None,
    *,
    role: str | None = None,
    selectable: bool = False,
) -> QLabel:
    label = QLabel(text, parent)
    label.setWordWrap(True)
    if role is not None:
        _set_ui_role(label, role)
    if selectable:
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByKeyboard)
    return label


def _card(parent: QWidget, *, quiet: bool = False) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(parent)
    _set_ui_role(frame, "quietCard" if quiet else "card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 16, 18, 17)
    layout.setSpacing(10)
    return frame, layout


def _add_section_heading(
    layout: QVBoxLayout,
    title: str,
    description: str | None = None,
) -> tuple[QLabel, QLabel | None]:
    title_label = _text_label(title, role="sectionTitle")
    layout.addWidget(title_label)
    description_label = None
    if description:
        description_label = _text_label(description, role="secondary")
        layout.addWidget(description_label)
    return title_label, description_label


def _scrollable_page(page: QWidget, owner: QWidget) -> QScrollArea:
    scroll = QScrollArea(owner)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setWidget(page)
    return scroll


def hotkey_from_qt_key(
    key: int, native_virtual_key: int, native_scan_code: int = 0
) -> str | None:
    """Translate a captured Windows key into a supported hotkey part."""
    # Qt normally receives the generic VK_CONTROL/VK_MENU values from Windows.
    # Right-side modifier keys are distinguished by their extended scan codes.
    # Accept the side-specific virtual keys too, because synthetic events and
    # some keyboard drivers provide those instead.
    if native_virtual_key == 0xA3 or (
        key == int(Qt.Key.Key_Control) and native_scan_code in {0xE01D, 0x11D}
    ):
        return "right_ctrl"
    if native_virtual_key == 0xA2 or (
        key == int(Qt.Key.Key_Control) and native_scan_code == 0x1D
    ):
        return "left_ctrl"
    if native_virtual_key == 0x5B:
        return "left_windows"
    if native_virtual_key == 0xA4 or (
        key == int(Qt.Key.Key_Alt) and native_scan_code == 0x38
    ):
        return "left_alt"
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
        self._pressed_parts: set[str] = set()
        self._can_capture = can_capture or (lambda: True)
        self.setAccessibleName(tr("Change push-to-talk key"))
        self.setAccessibleDescription(
            tr(
                "Press this button, then press Right Ctrl, a supported two-key "
                "combination, or F6 through F12."
            )
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
        self._pressed_parts.clear()
        self.setText(tr("Press a key or combination…"))
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
        self._pressed_parts.clear()
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
        if identifier is not None:
            self._pressed_parts.add(identifier)
        selected = hotkey_identifier_for_parts(self._pressed_parts)
        if selected is not None:
            self._captured_identifier = selected
            self.hotkey_captured.emit(selected)
            self.setText(tr("Release key…"))
            self.setAccessibleName(tr("Release the selected push-to-talk key"))
            event.accept()
            return
        if is_hotkey_part_prefix(self._pressed_parts):
            self.setText(tr("Press the second key…"))
            event.accept()
            return
        if identifier is None or self._pressed_parts:
            self._pressed_parts.clear()
            self.capture_rejected.emit(
                tr(
                    "Use Right Ctrl, Left Ctrl + Windows, Left Ctrl + Left Alt, "
                    "or F6 through F12."
                )
            )
            event.accept()
            return

    def keyReleaseEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if not self._capturing:
            super().keyReleaseEvent(event)
            return
        if event.isAutoRepeat():
            event.accept()
            return
        identifier = hotkey_from_qt_key(
            event.key(), event.nativeVirtualKey(), event.nativeScanCode()
        )
        if self._captured_identifier is None:
            if identifier is not None:
                self._pressed_parts.discard(identifier)
            if not self._pressed_parts:
                self.setText(tr("Press a key or combination…"))
        elif identifier in HOTKEY_PARTS[self._captured_identifier]:
            # Keep the global listener stopped until the selected key is
            # physically up. Restarting it on key-down can give pynput half of
            # the capture event and leave push-to-talk permanently pressed.
            self._finish_capture()
        event.accept()

    def retranslate_ui(self) -> None:
        self.setAccessibleDescription(
            tr(
                "Press this button, then press Right Ctrl, a supported two-key "
                "combination, or F6 through F12."
            )
        )
        if not self._capturing:
            self.setText(f"&{tr('Change…')}")
            self.setAccessibleName(tr("Change push-to-talk key"))
        elif self._captured_identifier is None:
            self.setText(tr("Press a key or combination…"))
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
        startup_available: bool = False,
    ) -> None:
        super().__init__()
        self._store = store
        self._save_settings = save_settings or store.save
        self._microphone_provider = microphone_provider or self._default_microphones
        self._can_change_input = can_change_input or (lambda: True)
        self._title = title
        self._active_model = active_model
        self._model_runtime = model_runtime
        self._startup_available = startup_available
        self._settings = UserSettings()
        self._settings_warning: str | None = None
        self._status_state = "starting"
        self._selected_hotkey = DEFAULT_HOTKEY
        self.setWindowTitle(tr("Settings"))
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setMinimumSize(640, 520)
        self.resize(760, 680)
        self.setAccessibleName(tr("Skrivi settings"))
        self.setAccessibleDescription(
            tr("Configure Skrivi and review its local privacy behaviour.")
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 18)
        root.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(16)
        header_copy = QVBoxLayout()
        header_copy.setSpacing(2)
        self._product_name = _text_label("Skrivi", self, role="eyebrow")
        header_copy.addWidget(self._product_name)
        self._heading = _text_label(tr("Settings"), self, role="windowTitle")
        self._heading.setAccessibleName(tr("Skrivi settings heading"))
        header_copy.addWidget(self._heading)
        self._header_description = _text_label(
            tr("Choose how Skrivi listens, looks and starts."),
            self,
            role="secondary",
        )
        header_copy.addWidget(self._header_description)
        header.addLayout(header_copy, 1)
        self._header_icon = QLabel(self)
        self._header_icon.setPixmap(QApplication.windowIcon().pixmap(46, 46))
        self._header_icon.setAccessibleName(tr("Skrivi logo"))
        header.addWidget(self._header_icon, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        self._warning = _text_label(parent=self, role="warning", selectable=True)
        self._warning.setAccessibleName(tr("Settings warning"))
        root.addWidget(self._warning)

        self.tabs = QTabWidget(self)
        self.tabs.setDocumentMode(True)
        self.tabs.setAccessibleName(tr("Settings sections"))
        self.tabs.addTab(self._general_page(), f"&{tr('General')}")
        self.model_panel = ModelManagerPanel(model_manager, model_runtime, self)
        self.model_panel.model_activated.connect(self._model_activated)
        self.tabs.addTab(self.model_panel, f"&{tr('Models')}")
        self.tabs.addTab(self._privacy_page(), f"&{tr('Privacy')}")
        self.tabs.addTab(self._about_page(), f"&{tr('About')}")
        root.addWidget(self.tabs, 1)
        self.manage_models_button.clicked.connect(lambda: self.tabs.setCurrentIndex(1))

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        self.buttons.setAccessibleName(tr("Settings actions"))
        self.buttons.accepted.connect(self._save)
        self.buttons.rejected.connect(self.reject)

        footer = QHBoxLayout()
        footer.setSpacing(12)
        self._save_hint = _text_label(
            tr("Ctrl+S saves changes"), self, role="secondary"
        )
        self._save_hint.setWordWrap(False)
        footer.addWidget(self._save_hint)
        footer.addStretch(1)
        footer.addWidget(self.buttons)
        root.addLayout(footer)

        save_button = self.buttons.button(QDialogButtonBox.StandardButton.Save)
        if save_button is not None:
            save_button.setProperty("buttonRole", "primary")
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
        page.setObjectName("settingsPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(6, 10, 6, 14)
        layout.setSpacing(14)

        self._status_card = QFrame(page)
        _set_ui_role(self._status_card, "quietCard")
        status_layout = QHBoxLayout(self._status_card)
        status_layout.setContentsMargins(16, 11, 16, 12)
        status_layout.setSpacing(12)
        self._status_dot = QLabel("●", self._status_card)
        self._status_dot.setObjectName("statusDot")
        self._status_dot.setProperty("statusState", self._status_state)
        self._status_dot.setAccessibleName(tr("Status symbol"))
        status_layout.addWidget(self._status_dot)
        status_copy = QVBoxLayout()
        status_copy.setSpacing(1)
        self._status_title = _text_label(
            tr("Current status"), self._status_card, role="secondary"
        )
        status_copy.addWidget(self._status_title)
        self._status = _text_label(
            tr("Starting"), self._status_card, role="value", selectable=True
        )
        self._status.setWordWrap(True)
        self._status.setAccessibleName(tr("Current dictation status"))
        status_copy.addWidget(self._status)
        status_layout.addLayout(status_copy, 1)
        layout.addWidget(self._status_card)

        self._dictation_card, dictation_layout = _card(page)
        self._dictation_title, self._dictation_description = _add_section_heading(
            dictation_layout,
            tr("Dictation"),
            tr("Choose what Skrivi listens for and how you start speaking."),
        )
        setup_layout = QFormLayout()
        setup_layout.setContentsMargins(0, 6, 0, 0)
        setup_layout.setHorizontalSpacing(18)
        setup_layout.setVerticalSpacing(10)
        setup_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        setup_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        self.language_combo = QComboBox(self._dictation_card)
        self.language_combo.setAccessibleName(tr("Dictation language"))
        for label, mode in LANGUAGE_CHOICES:
            self.language_combo.addItem(tr(label), mode.value)
        self._language_label = QLabel(f"&{tr('Language')}:", self._dictation_card)
        self._language_label.setBuddy(self.language_combo)
        setup_layout.addRow(self._language_label, self.language_combo)
        self._language_help = _text_label(
            parent=self._dictation_card,
            role="secondary",
        )
        setup_layout.addRow(self._language_help)
        self.language_combo.currentIndexChanged.connect(self._set_language_help)

        self._model = self._value_label(tr("Speech model value"))
        model_row = QWidget(self._dictation_card)
        model_layout = QHBoxLayout(model_row)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.setSpacing(8)
        model_layout.addWidget(self._model, 1)
        self.manage_models_button = QPushButton(f"&{tr('Models…')}", model_row)
        self.manage_models_button.setAccessibleName(tr("Manage speech models"))
        model_layout.addWidget(self.manage_models_button)
        self._model_label = QLabel(f"{tr('Speech model')}:", self._dictation_card)
        setup_layout.addRow(self._model_label, model_row)

        microphone_row = QWidget(self._dictation_card)
        microphone_layout = QHBoxLayout(microphone_row)
        microphone_layout.setContentsMargins(0, 0, 0, 0)
        microphone_layout.setSpacing(8)
        self.microphone_combo = QComboBox(microphone_row)
        self.microphone_combo.setAccessibleName(tr("Microphone"))
        self.refresh_microphones_button = QPushButton(
            f"&{tr('Refresh')}", microphone_row
        )
        self.refresh_microphones_button.setAccessibleName(tr("Refresh microphones"))
        self.refresh_microphones_button.clicked.connect(self._refresh_microphones)
        microphone_layout.addWidget(self.microphone_combo, 1)
        microphone_layout.addWidget(self.refresh_microphones_button)
        self._microphone_label = QLabel(f"&{tr('Microphone')}:", self._dictation_card)
        self._microphone_label.setBuddy(self.microphone_combo)
        setup_layout.addRow(self._microphone_label, microphone_row)
        self._microphone_help = _text_label(
            parent=self._dictation_card, role="secondary"
        )
        self._microphone_help.setAccessibleName(tr("Microphone availability"))
        setup_layout.addRow(self._microphone_help)

        hotkey_row = QWidget(self._dictation_card)
        hotkey_layout = QHBoxLayout(hotkey_row)
        hotkey_layout.setContentsMargins(0, 0, 0, 0)
        hotkey_layout.setSpacing(8)
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
        self._hotkey_label = QLabel(f"{tr('Push-to-talk key')}:", self._dictation_card)
        setup_layout.addRow(self._hotkey_label, hotkey_row)
        self._hotkey_help = _text_label(
            tr(
                "Recommended for laptops: Left Ctrl + Windows. Right Ctrl and "
                "Left Ctrl + Left Alt also work. F6 through F12 can conflict "
                "with shortcuts in other apps."
            ),
            self._dictation_card,
            role="secondary",
        )
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
        dictation_layout.addLayout(setup_layout)
        layout.addWidget(self._dictation_card)

        self._application_card, application_layout = _card(page)
        self._application_title, self._application_description = _add_section_heading(
            application_layout,
            tr("Application"),
            tr("Choose how Skrivi looks and behaves when Windows starts."),
        )
        application_form = QFormLayout()
        application_form.setContentsMargins(0, 6, 0, 2)
        application_form.setHorizontalSpacing(18)
        application_form.setVerticalSpacing(10)
        application_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        application_form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        self.interface_language_combo = QComboBox(self._application_card)
        self.interface_language_combo.setAccessibleName(tr("Interface language"))
        for label, language in INTERFACE_LANGUAGE_CHOICES:
            self.interface_language_combo.addItem(tr(label), language.value)
        self._interface_language_label = QLabel(
            f"{tr('Interface language')}:", self._application_card
        )
        self._interface_language_label.setBuddy(self.interface_language_combo)
        application_form.addRow(
            self._interface_language_label, self.interface_language_combo
        )
        self._interface_help = _text_label(
            tr("Interface language updates immediately."),
            self._application_card,
            role="secondary",
        )
        application_form.addRow(self._interface_help)
        application_layout.addLayout(application_form)

        self.overlay_checkbox = QCheckBox(
            f"&{tr('Show the compact status overlay while dictating')}",
            self._application_card,
        )
        self.overlay_checkbox.setAccessibleName(tr("Show dictation status overlay"))
        self.overlay_checkbox.setAccessibleDescription(
            tr(
                "Show a non-activating message while Skrivi loads, listens and "
                "transcribes."
            )
        )
        application_layout.addWidget(self.overlay_checkbox)

        self.startup_checkbox = QCheckBox(
            f"&{tr('Start Skrivi automatically when I sign in')}",
            self._application_card,
        )
        self.startup_checkbox.setAccessibleName(tr("Start Skrivi automatically"))
        self.startup_checkbox.setEnabled(self._startup_available)
        application_layout.addWidget(self.startup_checkbox)
        self._startup_help = _text_label(
            parent=self._application_card, role="secondary"
        )
        self._startup_help.setAccessibleName(tr("Automatic startup guidance"))
        application_layout.addWidget(self._startup_help)
        self._set_startup_help()
        layout.addWidget(self._application_card)
        layout.addStretch(1)

        return _scrollable_page(page, self)

    @staticmethod
    def _value_label(accessible_name: str) -> QLabel:
        label = _text_label(role="value")
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByKeyboard)
        label.setAccessibleName(accessible_name)
        return label

    def _privacy_page(self) -> QWidget:
        page = QWidget(self)
        page.setObjectName("settingsPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(6, 16, 6, 14)
        layout.setSpacing(14)

        self._privacy_title = _text_label(
            tr("Your words stay yours."), page, role="pageTitle"
        )
        layout.addWidget(self._privacy_title)
        self._privacy = _text_label(
            tr(
                "Skrivi is designed to turn your speech into text without creating "
                "an account or sending your dictation to us."
            ),
            page,
            role="secondary",
            selectable=True,
        )
        self._privacy.setAccessibleName(tr("Skrivi privacy summary"))
        layout.addWidget(self._privacy)

        facts = QGridLayout()
        facts.setHorizontalSpacing(12)
        facts.setVerticalSpacing(12)
        fact_copy = (
            (
                "Processed on this PC",
                "Your recording is transcribed locally by the speech model installed "
                "on this computer.",
            ),
            (
                "Nothing saved by Skrivi",
                "Skrivi does not keep a history of recordings or dictated text.",
            ),
            (
                "No account or clipboard",
                "You do not sign in, and dictated text is inserted without using the "
                "Windows clipboard.",
            ),
            (
                "Works offline after setup",
                "Internet is needed to download a speech model. Installed models work "
                "without it.",
            ),
        )
        self._privacy_facts: list[tuple[QLabel, QLabel, str, str]] = []
        for index, (title, body) in enumerate(fact_copy):
            fact_card, fact_layout = _card(page, quiet=True)
            title_label, _ = _add_section_heading(fact_layout, tr(title))
            body_label = _text_label(
                tr(body), fact_card, role="secondary", selectable=True
            )
            fact_layout.addWidget(body_label)
            facts.addWidget(fact_card, index // 2, index % 2)
            self._privacy_facts.append((title_label, body_label, title, body))
        layout.addLayout(facts)

        self._privacy_boundary_card, boundary_layout = _card(page)
        self._privacy_boundary_title, _ = _add_section_heading(
            boundary_layout, tr("One important boundary")
        )
        self._privacy_boundary = _text_label(
            tr(
                "The app receiving your text, such as Word, a browser or a school "
                "platform, may save or sync it according to that app's own settings."
            ),
            self._privacy_boundary_card,
            role="secondary",
            selectable=True,
        )
        boundary_layout.addWidget(self._privacy_boundary)
        layout.addWidget(self._privacy_boundary_card)

        privacy_actions = QHBoxLayout()
        self.privacy_details_button = QPushButton(
            f"&{tr('Read full privacy details')}", page
        )
        self.privacy_details_button.setAccessibleName(tr("Open privacy documentation"))
        self.privacy_details_button.clicked.connect(self._open_privacy_details)
        privacy_actions.addWidget(self.privacy_details_button)
        privacy_actions.addStretch(1)
        layout.addLayout(privacy_actions)
        layout.addStretch(1)
        return _scrollable_page(page, self)

    def _about_page(self) -> QWidget:
        page = QWidget(self)
        page.setObjectName("settingsPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(6, 16, 6, 14)
        layout.setSpacing(14)

        about_header = QHBoxLayout()
        about_header.setSpacing(16)
        self._about_icon = QLabel(page)
        self._about_icon.setPixmap(QApplication.windowIcon().pixmap(60, 60))
        self._about_icon.setAccessibleName(tr("Skrivi logo"))
        about_header.addWidget(self._about_icon, 0, Qt.AlignmentFlag.AlignTop)
        about_copy = QVBoxLayout()
        about_copy.setSpacing(3)
        self._about_title = _text_label("Skrivi", page, role="pageTitle")
        about_copy.addWidget(self._about_title)
        self._about_tagline = _text_label(
            tr("Get your thoughts onto the page."), page, role="secondary"
        )
        about_copy.addWidget(self._about_tagline)
        self._about_version = _text_label(
            self._title, page, role="statusBadge", selectable=True
        )
        self._about_version.setWordWrap(False)
        self._about_version.setAccessibleName(tr("Skrivi version"))
        about_copy.addWidget(self._about_version, 0, Qt.AlignmentFlag.AlignLeft)
        about_header.addLayout(about_copy, 1)
        layout.addLayout(about_header)

        self._about_card, about_layout = _card(page)
        self._about_section_title, _ = _add_section_heading(
            about_layout, tr("Free, local and open source")
        )
        self._about = _text_label(
            tr(
                "Skrivi is a small speech-to-text tool. It transcribes your own words "
                "locally and does not generate answers or rewrite what you say."
            ),
            self._about_card,
            role="secondary",
            selectable=True,
        )
        self._about.setAccessibleName(tr("About Skrivi"))
        about_layout.addWidget(self._about)
        layout.addWidget(self._about_card)

        self._links_card, links_layout = _card(page, quiet=True)
        self._links_title, self._links_description = _add_section_heading(
            links_layout,
            tr("Learn more"),
            tr("Open documentation in your web browser."),
        )
        links = QHBoxLayout()
        links.setSpacing(8)
        self.website_button = QPushButton(f"&{tr('Website')}", self._links_card)
        self.website_button.setAccessibleName(tr("Open Skrivi website"))
        self.website_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(WEBSITE_URL))
        )
        self.source_button = QPushButton(f"&{tr('Source code')}", self._links_card)
        self.source_button.setAccessibleName(tr("Open Skrivi source code"))
        self.source_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(SOURCE_URL))
        )
        self.notices_button = QPushButton(
            f"&{tr('Third-party licences')}", self._links_card
        )
        self.notices_button.setAccessibleName(tr("Open third-party licence notices"))
        self.notices_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(NOTICES_URL))
        )
        links.addWidget(self.website_button)
        links.addWidget(self.source_button)
        links.addWidget(self.notices_button)
        links.addStretch(1)
        links_layout.addLayout(links)
        layout.addWidget(self._links_card)
        layout.addStretch(1)
        return _scrollable_page(page, self)

    @Slot()
    def _open_privacy_details(self) -> None:
        url = (
            PRIVACY_URL_NB
            if current_interface_language() is InterfaceLanguage.NORWEGIAN_BOKMAL
            else PRIVACY_URL
        )
        QDesktopServices.openUrl(QUrl(url))

    def _set_hotkey(self, identifier: str) -> None:
        try:
            self._selected_hotkey = validate_hotkey(identifier)
        except HotkeyValidationError as error:
            self._hotkey_help.setText(str(error))
            return
        self._hotkey.setText(tr(hotkey_display_name(self._selected_hotkey)))
        self._hotkey_help.setText(
            tr(
                "Recommended for laptops: Left Ctrl + Windows. Right Ctrl and "
                "Left Ctrl + Left Alt also work. F6 through F12 can conflict "
                "with shortcuts in other apps."
            )
        )

    def _set_startup_help(self) -> None:
        if self._startup_available:
            self._startup_help.setText(
                tr(
                    "Skrivi starts quietly in the system tray. Keep a portable "
                    "copy in a permanent folder while this is enabled."
                )
            )
        else:
            self._startup_help.setText(
                tr("Automatic startup is unavailable in this Skrivi build.")
            )

    def _select_language(self, language: LanguageMode) -> None:
        index = self.language_combo.findData(language.value)
        self.language_combo.setCurrentIndex(max(index, 0))

    @Slot(int)
    def _set_language_help(self, _index: int = -1) -> None:
        descriptions = {
            LanguageMode.AUTOMATIC.value: (
                "Detects Norwegian or English for each dictation. Best for most people."
            ),
            LanguageMode.ENGLISH.value: "Always listens for English.",
            LanguageMode.NORWEGIAN.value: "Always listens for Norwegian.",
        }
        key = self.language_combo.currentData() or LanguageMode.AUTOMATIC.value
        self._language_help.setText(tr(descriptions[str(key)]))
        self._language_help.setAccessibleName(tr("Dictation language guidance"))

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
        self.setWindowTitle(tr("Settings"))
        self.setAccessibleName(tr("Skrivi settings"))
        self.setAccessibleDescription(
            tr("Configure Skrivi and review its local privacy behaviour.")
        )
        self._heading.setText(tr("Settings"))
        self._heading.setAccessibleName(tr("Skrivi settings heading"))
        self._header_description.setText(
            tr("Choose how Skrivi listens, looks and starts.")
        )
        self._header_icon.setAccessibleName(tr("Skrivi logo"))
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
        self._save_hint.setText(tr("Ctrl+S saves changes"))

        self._status_title.setText(tr("Current status"))
        if self._status_state == "starting":
            self._status.setText(tr("Starting"))
        self._status.setAccessibleName(tr("Current dictation status"))
        self._status_dot.setAccessibleName(tr("Status symbol"))
        self._dictation_title.setText(tr("Dictation"))
        self._dictation_description.setText(
            tr("Choose what Skrivi listens for and how you start speaking.")
        )
        self._replace_choices(self.language_combo, LANGUAGE_CHOICES)
        self.language_combo.setAccessibleName(tr("Dictation language"))
        self._language_label.setText(f"&{tr('Language')}:")
        self._set_language_help()
        self._model_label.setText(f"{tr('Speech model')}:")
        self._model.setAccessibleName(tr("Speech model value"))
        self.manage_models_button.setText(f"&{tr('Models…')}")
        self.manage_models_button.setAccessibleName(tr("Manage speech models"))
        self._application_title.setText(tr("Application"))
        self._application_description.setText(
            tr("Choose how Skrivi looks and behaves when Windows starts.")
        )
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
        self.startup_checkbox.setText(
            f"&{tr('Start Skrivi automatically when I sign in')}"
        )
        self.startup_checkbox.setAccessibleName(tr("Start Skrivi automatically"))
        self._startup_help.setAccessibleName(tr("Automatic startup guidance"))
        self._set_startup_help()

        self._privacy_title.setText(tr("Your words stay yours."))
        self._privacy.setText(
            tr(
                "Skrivi is designed to turn your speech into text without creating "
                "an account or sending your dictation to us."
            )
        )
        self._privacy.setAccessibleName(tr("Skrivi privacy summary"))
        for title_label, body_label, title, body in self._privacy_facts:
            title_label.setText(tr(title))
            body_label.setText(tr(body))
        self._privacy_boundary_title.setText(tr("One important boundary"))
        self._privacy_boundary.setText(
            tr(
                "The app receiving your text, such as Word, a browser or a school "
                "platform, may save or sync it according to that app's own settings."
            )
        )
        self.privacy_details_button.setText(f"&{tr('Read full privacy details')}")
        self.privacy_details_button.setAccessibleName(tr("Open privacy documentation"))

        self._about_icon.setAccessibleName(tr("Skrivi logo"))
        self._about_tagline.setText(tr("Get your thoughts onto the page."))
        self._about_version.setAccessibleName(tr("Skrivi version"))
        self._about_section_title.setText(tr("Free, local and open source"))
        self._about.setText(
            tr(
                "Skrivi is a small speech-to-text tool. It transcribes your own words "
                "locally and does not generate answers or rewrite what you say."
            )
        )
        self._about.setAccessibleName(tr("About Skrivi"))
        self._links_title.setText(tr("Learn more"))
        self._links_description.setText(tr("Open documentation in your web browser."))
        self.website_button.setText(f"&{tr('Website')}")
        self.website_button.setAccessibleName(tr("Open Skrivi website"))
        self.source_button.setText(f"&{tr('Source code')}")
        self.source_button.setAccessibleName(tr("Open Skrivi source code"))
        self.notices_button.setText(f"&{tr('Third-party licences')}")
        self.notices_button.setAccessibleName(tr("Open third-party licence notices"))
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
        self.startup_checkbox.setChecked(self._settings.start_with_system)
        self._select_language(self._settings.language)
        self._set_language_help()
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
        self._status_dot.setProperty("statusState", state)
        self._status_dot.style().unpolish(self._status_dot)
        self._status_dot.style().polish(self._status_dot)
        self._status_dot.update()

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
            start_with_system=self.startup_checkbox.isChecked(),
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
