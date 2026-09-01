from __future__ import annotations

from string import Formatter

import pytest

from whisper_dictate.i18n import (
    NORWEGIAN_BOKMAL,
    InterfaceLanguage,
    add_interface_language_listener,
    interface_language_from_locale,
    set_interface_language,
    tr,
)


@pytest.fixture(autouse=True)
def reset_interface_language():
    set_interface_language(InterfaceLanguage.ENGLISH)
    yield
    set_interface_language(InterfaceLanguage.ENGLISH)


@pytest.mark.parametrize("locale_name", ["nb_NO", "no-NO", "nn_NO", "NB-no"])
def test_norwegian_windows_locales_use_bokmal(locale_name: str) -> None:
    assert (
        interface_language_from_locale(locale_name)
        is InterfaceLanguage.NORWEGIAN_BOKMAL
    )


@pytest.mark.parametrize("locale_name", ["en_US", "sv_SE", "de-DE", ""])
def test_other_windows_locales_fall_back_to_english(locale_name: str) -> None:
    assert interface_language_from_locale(locale_name) is InterfaceLanguage.ENGLISH


def test_bokmal_translates_and_formats_interface_text() -> None:
    set_interface_language(InterfaceLanguage.NORWEGIAN_BOKMAL)

    assert tr("Settings") == "Innstillinger"
    assert tr("{title} Settings", title="Bragi") == "Innstillinger for Bragi"
    assert tr("Downloading {name}…", name="Small") == "Laster ned Small …"
    assert tr("English") == "English"


def test_unknown_text_is_safely_left_unchanged() -> None:
    set_interface_language(InterfaceLanguage.NORWEGIAN_BOKMAL)

    assert tr("A future message") == "A future message"


def test_bokmal_translations_preserve_format_fields() -> None:
    formatter = Formatter()

    for source, translation in NORWEGIAN_BOKMAL.items():
        source_fields = {
            field for _, field, _, _ in formatter.parse(source) if field is not None
        }
        translated_fields = {
            field
            for _, field, _, _ in formatter.parse(translation)
            if field is not None
        }
        assert translated_fields == source_fields, source


def test_language_change_notifies_live_interface_listeners() -> None:
    events: list[str] = []

    class Interface:
        def retranslate(self) -> None:
            events.append(tr("Settings"))

    interface = Interface()
    add_interface_language_listener(interface.retranslate)

    set_interface_language(InterfaceLanguage.NORWEGIAN_BOKMAL)
    set_interface_language(InterfaceLanguage.ENGLISH)

    assert events == ["Innstillinger", "Settings"]
