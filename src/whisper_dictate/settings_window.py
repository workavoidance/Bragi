from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from whisper_dictate.settings import (
    SettingsLoadResult,
    SettingsStore,
    SettingsWriteError,
    UserSettings,
)


class SettingsWindow(QDialog):
    """Keyboard-operable shell for Bragi's versioned settings."""

    settings_saved = Signal(object)

    def __init__(self, store: SettingsStore, *, title: str = "Bragi") -> None:
        super().__init__()
        self._store = store
        self._settings = UserSettings()
        self.setWindowTitle(f"{title} Settings")
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setMinimumSize(560, 480)
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

        setup_group = QGroupBox("Current dictation setup", page)
        setup_layout = QFormLayout(setup_group)
        self._language = self._value_label("Language value")
        self._model = self._value_label("Speech model value")
        self._hotkey = self._value_label("Push-to-talk key value")
        self._microphone = self._value_label("Microphone value")
        setup_layout.addRow("Language:", self._language)
        setup_layout.addRow("Speech model:", self._model)
        setup_layout.addRow("Push-to-talk key:", self._hotkey)
        setup_layout.addRow("Microphone:", self._microphone)
        helper = QLabel(
            "Language, model, hotkey and microphone controls will be added in "
            "the next configuration milestones.",
            setup_group,
        )
        helper.setWordWrap(True)
        helper.setAccessibleName("Configuration availability")
        setup_layout.addRow(helper)
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
        return page

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

    def reload(self) -> SettingsLoadResult:
        result = self._store.load()
        self._settings = result.settings
        self._warning.setText(result.warning or "")
        self._warning.setVisible(result.warning is not None)
        self.overlay_checkbox.setChecked(self._settings.overlay_enabled)
        # Issue #6 will make these stored choices live. Until then, report the
        # pipeline that is actually running rather than implying manual edits
        # to settings.json have taken effect.
        self._language.setText("Automatic English and Norwegian")
        self._model.setText("small")
        self._hotkey.setText("Right Ctrl")
        self._microphone.setText("Windows default")
        return result

    @Slot()
    def show_settings(self) -> None:
        self.reload()
        self.show()
        self.raise_()
        self.activateWindow()
        self.tabs.setCurrentIndex(0)
        self.overlay_checkbox.setFocus(Qt.FocusReason.ShortcutFocusReason)

    @Slot(str, str)
    def set_status(self, state: str, text: str) -> None:
        del state
        self._status.setText(text)

    @Slot()
    def _save(self) -> None:
        updated = replace(
            self._settings,
            overlay_enabled=self.overlay_checkbox.isChecked(),
        )
        try:
            self._store.save(updated)
        except SettingsWriteError:
            QMessageBox.critical(
                self,
                "Settings could not be saved",
                "Bragi could not save settings safely. Your previous settings "
                "have not been replaced.",
            )
            return
        self._settings = updated
        self.settings_saved.emit(updated)
        self.accept()
