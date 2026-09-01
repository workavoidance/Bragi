from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from whisper_dictate.application import bragi_icon


class TrayIcon:
    """Bragi's Qt system tray menu."""

    def __init__(
        self,
        on_exit: Callable[[], None],
        *,
        on_settings: Callable[[], None],
        on_retry_model: Callable[[], object] | None = None,
        title: str = "Bragi",
        preview_actions: Mapping[str, Callable[[], None]] | None = None,
    ) -> None:
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("create_application() must be called before the UI")
        self._on_exit = on_exit
        self._on_settings = on_settings
        self._on_retry_model = on_retry_model
        self._title = title
        self._preview_actions = dict(preview_actions or {})

        self._menu = QMenu()
        self._menu.setAccessibleName("Bragi tray menu")
        title_action = self._menu.addAction(title)
        title_action.setEnabled(False)
        self._status_action = self._menu.addAction("Status: Starting")
        self._status_action.setEnabled(False)
        self._menu.addSeparator()

        self.settings_action = QAction("&Settings…", self._menu)
        self.settings_action.setToolTip("Open Bragi settings")
        self.settings_action.triggered.connect(self._settings_clicked)
        self._menu.addAction(self.settings_action)

        self.retry_model_action = QAction("&Retry speech model", self._menu)
        self.retry_model_action.setAccessibleName("Retry speech model")
        self.retry_model_action.setToolTip(
            "Try loading the selected local speech model again"
        )
        self.retry_model_action.setVisible(False)
        self.retry_model_action.triggered.connect(self._retry_model_clicked)
        self._menu.addAction(self.retry_model_action)

        if self._preview_actions:
            preview_menu = self._menu.addMenu("Preview &state")
            for label, callback in self._preview_actions.items():
                action = preview_menu.addAction(label)
                action.triggered.connect(
                    lambda _checked=False, callback=callback: callback()
                )

        self._menu.addSeparator()
        self.exit_action = QAction("E&xit", self._menu)
        self.exit_action.triggered.connect(self._exit_clicked)
        self._menu.addAction(self.exit_action)

        self._icon = QSystemTrayIcon(bragi_icon(), app)
        self._icon.setToolTip(title)
        self._icon.setContextMenu(self._menu)
        self._icon.activated.connect(self._activated)

    @property
    def menu(self) -> QMenu:
        return self._menu

    def start(self) -> None:
        self._icon.show()

    def stop(self) -> None:
        self._icon.hide()

    def set_status(self, state: str, text: str) -> None:
        self._status_action.setText(f"Status: {text}")
        self._icon.setToolTip(f"{self._title}\n{text}")
        self.retry_model_action.setVisible(
            state == "model_error" and self._on_retry_model is not None
        )

    def _settings_clicked(self, checked: bool = False) -> None:
        del checked
        self._on_settings()

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
