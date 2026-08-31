from __future__ import annotations

from collections.abc import Callable

from whisper_dictate.indicator import FloatingIndicator
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
    indicator = FloatingIndicator(title=preview_title)
    tray = TrayIcon(
        indicator.request_exit,
        title=preview_title,
        preview_actions=preview_actions(indicator),
    )

    def shutdown() -> None:
        tray.stop()

    indicator.set_exit_handler(shutdown)
    tray.start()
    indicator.post("ready", "Preview ready — choose a state from the tray icon")
    indicator.run()
