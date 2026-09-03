from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtCore import QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from whisper_dictate.application import skrivi_icon
from whisper_dictate.i18n import (
    InterfaceLanguage,
    add_interface_language_listener,
    current_interface_language,
    tr,
)

FEEDBACK_URL = "https://skrivi.no/feedback/"


def _feedback_text() -> str:
    if current_interface_language() is InterfaceLanguage.NORWEGIAN_BOKMAL:
        return "Gi tilbakemelding"
    return "Give feedback"


def _feedback_tooltip() -> str:
    if current_interface_language() is InterfaceLanguage.NORWEGIAN_BOKMAL:
        return "Åpne Skrivi-siden for tilbakemeldinger i nettleseren"
    return "Open the Skrivi feedback page in your web browser"


def open_feedback_page() -> None:
    QDesktopServices.openUrl(QUrl(FEEDBACK_URL))


class TrayIcon:
    """Skrivi's Qt system tray menu."""

    def __init__(
        self,
        on_exit: Callable[[], None],
        *,
        on_settings: Callable[[], None],
        on_retry_model: Callable[[], object] | None = None,
        on_feedback: Callable[[], None] | None = None,
        title: str = "Skrivi",
        preview_actions: Mapping[str, Callable[[], None]] | None = None,
    ) -> None:
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("create_application() must be called before the UI")
        self._on_exit = on_exit
        self._on_settings = on_settings
        self._on_retry_model = on_retry_model
        self._on_feedback = on_feedback or open_feedback_page
        self._title = title
        self._preview_actions = dict(preview_actions or {})
        self._status_state = "starting"
        self._status_text = tr("Starting")
        self._preview_menu = None
        self._preview_action_items: list[tuple[str, QAction]] = []

        self._menu = QMenu()
        self._menu.setAccessibleName(tr("Skrivi tray menu"))
        title_action = self._menu.addAction(title)
        title_action.setEnabled(False)
        self._status_action = self._menu.addAction(
            tr("Status: {text}", text=tr("Starting"))
        )
        self._status_action.setEnabled(False)
        self._menu.addSeparator()

        self.settings_action = QAction(f"&{tr('Settings')}…", self._menu)
        self.settings_action.setToolTip(tr("Open Skrivi settings"))
        self.settings_action.triggered.connect(self._settings_clicked)
        self._menu.addAction(self.settings_action)

        self.feedback_action = QAction(f"&{_feedback_text()}", self._menu)
        self.feedback_action.setToolTip(_feedback_tooltip())
        self.feedback_action.triggered.connect(self._feedback_clicked)
        self._menu.addAction(self.feedback_action)

        self.retry_model_action = QAction(f"&{tr('Retry speech model')}", self._menu)
        self.retry_model_action.setToolTip(
            tr("Try loading the selected local speech model again")
        )
        self.retry_model_action.setVisible(False)
        self.retry_model_action.triggered.connect(self._retry_model_clicked)
        self._menu.addAction(self.retry_model_action)

        if self._preview_actions:
            self._preview_menu = self._menu.addMenu(f"&{tr('Preview state')}")
            for label, callback in self._preview_actions.items():
                action = self._preview_menu.addAction(tr(label))
                self._preview_action_items.append((label, action))
                action.triggered.connect(
                    lambda _checked=False, callback=callback: callback()
                )

        self._menu.addSeparator()
        self.exit_action = QAction(f"&{tr('Exit')}", self._menu)
        self.exit_action.triggered.connect(self._exit_clicked)
        self._menu.addAction(self.exit_action)

        self._icon = QSystemTrayIcon(skrivi_icon(), app)
        self._icon.setToolTip(title)
        self._icon.setContextMenu(self._menu)
        self._icon.activated.connect(self._activated)
        add_interface_language_listener(self.retranslate_ui)

    @property
    def menu(self) -> QMenu:
        return self._menu

    def start(self) -> None:
        self._icon.show()

    def stop(self) -> None:
        self._icon.hide()

    def set_status(self, state: str, text: str) -> None:
        self._status_state = state
        self._status_text = text
        self._status_action.setText(tr("Status: {text}", text=text))
        self._icon.setToolTip(f"{self._title}\n{text}")
        self.retry_model_action.setVisible(
            state == "model_error" and self._on_retry_model is not None
        )

    def retranslate_ui(self) -> None:
        self._menu.setAccessibleName(tr("Skrivi tray menu"))
        self.settings_action.setText(f"&{tr('Settings')}…")
        self.settings_action.setToolTip(tr("Open Skrivi settings"))
        self.feedback_action.setText(f"&{_feedback_text()}")
        self.feedback_action.setToolTip(_feedback_tooltip())
        self.retry_model_action.setText(f"&{tr('Retry speech model')}")
        self.retry_model_action.setToolTip(
            tr("Try loading the selected local speech model again")
        )
        if self._preview_menu is not None:
            self._preview_menu.setTitle(f"&{tr('Preview state')}")
        for label, action in self._preview_action_items:
            action.setText(tr(label))
        self.exit_action.setText(f"&{tr('Exit')}")
        self.set_status(self._status_state, self._status_text)

    def _settings_clicked(self, checked: bool = False) -> None:
        del checked
        self._on_settings()

    def _feedback_clicked(self, checked: bool = False) -> None:
        del checked
        self._on_feedback()

    def _exit_clicked(self, checked: bool = False) -> None:
        del checked
        self._on_exit()

    def _retry_model_clicked(self, checked: bool = False) -> None:
        del checked
        if self._on_retry_model is not None:
            self._on_retry_model()

    def _activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_settings()
