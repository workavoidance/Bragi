from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from whisper_dictate.application import create_application
from whisper_dictate.i18n import InterfaceLanguage, set_interface_language
from whisper_dictate.tray import FEEDBACK_URL, TrayIcon


def _application():
    return create_application("Skrivi feedback tests")


def test_feedback_action_opens_explicit_feedback_callback() -> None:
    _application()
    events: list[str] = []
    tray = TrayIcon(
        lambda: None,
        on_settings=lambda: None,
        on_feedback=lambda: events.append("feedback"),
    )

    assert FEEDBACK_URL == "https://skrivi.no/feedback/"
    assert tray.feedback_action.text().replace("&", "") == "Give feedback"
    assert tray.feedback_action.toolTip() == (
        "Open the Skrivi feedback page in your web browser"
    )

    tray.feedback_action.trigger()

    assert events == ["feedback"]


def test_feedback_action_retranslates_to_norwegian() -> None:
    _application()
    tray = TrayIcon(lambda: None, on_settings=lambda: None, on_feedback=lambda: None)
    try:
        set_interface_language(InterfaceLanguage.NORWEGIAN_BOKMAL)

        assert tray.feedback_action.text().replace("&", "") == "Gi tilbakemelding"
        assert tray.feedback_action.toolTip() == (
            "Åpne Skrivi-siden for tilbakemeldinger i nettleseren"
        )
    finally:
        set_interface_language(InterfaceLanguage.ENGLISH)
