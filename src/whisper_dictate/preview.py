from __future__ import annotations

from collections.abc import Callable

from whisper_dictate.application import create_application
from whisper_dictate.indicator import FloatingIndicator
from whisper_dictate.settings import SettingsStore
from whisper_dictate.settings_window import SettingsWindow
from whisper_dictate.tray import TrayIcon

PREVIEW_STATES = (
    ("Loading", "loading", None),
    ("Ready", "ready", None),
    ("Recording", "recording", None),
    ("Transcribing", "transcribing", None),
    ("No speech", "empty", None),
    ("Error", "error", "Preview error: no user data was involved"),
)


def preview_actions(indicator: FloatingIndicator) -> dict[str, Callable[[], None]]:
    actions = {}
    for label, state, detail in PREVIEW_STATES:
        actions[label] = lambda state=state, detail=detail: indicator.post(
            state, detail
        )
    return actions


def run_preview(title: str) -> None:
    preview_title = title.replace(" DEV ", " PREVIEW ")
    _application = create_application(preview_title)
    settings_store = SettingsStore.for_user(development=True)
    settings = settings_store.load().settings
    indicator = FloatingIndicator(title=preview_title, enabled=settings.overlay_enabled)
    settings_window = SettingsWindow(settings_store, title=preview_title)
    tray = TrayIcon(
        indicator.request_exit,
        on_settings=settings_window.show_settings,
        title=preview_title,
        preview_actions=preview_actions(indicator),
    )
    indicator.status_changed.connect(tray.set_status)
    indicator.status_changed.connect(settings_window.set_status)
    settings_window.settings_saved.connect(
        lambda saved: indicator.set_enabled(saved.overlay_enabled)
    )

    def shutdown() -> None:
        tray.stop()

    indicator.set_exit_handler(shutdown)
    tray.start()
    indicator.post("ready", "Preview ready — choose a state from the tray icon")
    indicator.run()
