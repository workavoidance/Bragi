from whisper_dictate.windows_input import WindowsTextInjector


def test_utf16_units_support_norwegian_and_surrogate_pairs() -> None:
    text = "Blåbær 😊"
    units = WindowsTextInjector._utf16_units(text)
    rebuilt = b"".join(unit.to_bytes(2, "little") for unit in units).decode("utf-16-le")
    assert rebuilt == text
