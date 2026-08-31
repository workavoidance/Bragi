from __future__ import annotations

import json

import pytest

from whisper_dictate.settings import (
    CURRENT_SCHEMA_VERSION,
    INVALID_WARNING,
    MALFORMED_WARNING,
    NEWER_VERSION_WARNING,
    LanguageMode,
    SettingsStore,
    SettingsValidationError,
    SettingsWriteError,
    UserSettings,
)


def defaults_document() -> dict[str, object]:
    return UserSettings().to_document()


def test_defaults_match_the_existing_product_behaviour() -> None:
    settings = UserSettings()

    assert settings.schema_version == CURRENT_SCHEMA_VERSION
    assert settings.language is LanguageMode.AUTOMATIC
    assert settings.model == "small"
    assert settings.hotkey == "right_ctrl"
    assert settings.microphone == "windows_default"
    assert settings.overlay_enabled is True


def test_missing_file_returns_defaults_without_warning(tmp_path) -> None:
    result = SettingsStore(tmp_path / "settings.json").load()

    assert result.settings == UserSettings()
    assert result.warning is None
    assert result.recovered_with_defaults is False


def test_settings_survive_save_and_reload(tmp_path) -> None:
    store = SettingsStore(tmp_path / "settings.json")
    expected = UserSettings(
        language=LanguageMode.NORWEGIAN,
        model="base",
        hotkey="f8",
        microphone="USB microphone æøå",
        overlay_enabled=False,
    )

    store.save(expected)
    result = store.load()

    assert result.settings == expected
    assert result.warning is None
    assert json.loads(store.path.read_text(encoding="utf-8")) == expected.to_document()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("language", "fr"),
        ("model", ""),
        ("hotkey", " right_ctrl"),
        ("microphone", "bad\x00device"),
        ("overlay_enabled", "yes"),
    ],
)
def test_invalid_values_fall_back_with_a_generic_warning(
    tmp_path, field: str, value: object
) -> None:
    document = defaults_document()
    document[field] = value
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    result = SettingsStore(path).load()

    assert result.settings == UserSettings()
    assert result.warning == INVALID_WARNING
    if str(value):
        assert str(value) not in result.warning


def test_malformed_or_partial_json_is_preserved_and_defaults_are_used(tmp_path) -> None:
    path = tmp_path / "settings.json"
    broken = '{"schema_version": 1, "language":'
    path.write_text(broken, encoding="utf-8")

    result = SettingsStore(path).load()

    assert result.settings == UserSettings()
    assert result.warning == MALFORMED_WARNING
    assert path.read_text(encoding="utf-8") == broken


def test_unknown_privacy_sensitive_fields_are_never_accepted(tmp_path) -> None:
    document = defaults_document()
    document["transcript"] = "private dictated content"
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    result = SettingsStore(path).load()

    assert result.settings == UserSettings()
    assert result.warning == INVALID_WARNING
    assert "private dictated content" not in result.warning


def test_newer_schema_is_preserved_and_defaults_are_used(tmp_path) -> None:
    document = defaults_document()
    document["schema_version"] = CURRENT_SCHEMA_VERSION + 1
    original = json.dumps(document)
    path = tmp_path / "settings.json"
    path.write_text(original, encoding="utf-8")

    result = SettingsStore(path).load()

    assert result.settings == UserSettings()
    assert result.warning == NEWER_VERSION_WARNING
    assert path.read_text(encoding="utf-8") == original


def test_unversioned_v0_document_is_migrated_in_memory(tmp_path) -> None:
    legacy = {
        "language_mode": "no",
        "model_name": "base",
        "hotkey": "f9",
        "microphone": "windows_default",
        "show_overlay": False,
    }
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(legacy), encoding="utf-8")

    result = SettingsStore(path).load()

    assert result.settings == UserSettings(
        language=LanguageMode.NORWEGIAN,
        model="base",
        hotkey="f9",
        microphone="windows_default",
        overlay_enabled=False,
    )
    assert result.migrated_from == 0
    assert result.warning is None
    assert json.loads(path.read_text(encoding="utf-8")) == legacy


def test_save_rejects_an_invalid_directly_constructed_model(tmp_path) -> None:
    store = SettingsStore(tmp_path / "settings.json")

    with pytest.raises(SettingsValidationError):
        store.save(UserSettings(model=""))

    assert not store.path.exists()


def test_save_rejects_a_non_integer_schema_version(tmp_path) -> None:
    store = SettingsStore(tmp_path / "settings.json")

    with pytest.raises(SettingsValidationError):
        store.save(UserSettings(schema_version=1.0))

    assert not store.path.exists()


def test_failed_atomic_replace_preserves_the_previous_file(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    store.save(UserSettings())
    original = path.read_bytes()

    def fail_replace(source, destination) -> None:
        del source, destination
        raise OSError("simulated interruption")

    monkeypatch.setattr("whisper_dictate.settings.os.replace", fail_replace)

    with pytest.raises(SettingsWriteError):
        store.save(UserSettings(model="base"))

    assert path.read_bytes() == original
    assert list(tmp_path.glob("*.tmp")) == []


def test_directory_creation_failure_is_reported_as_a_safe_write_error(
    tmp_path, monkeypatch
) -> None:
    store = SettingsStore(tmp_path / "missing" / "settings.json")

    def fail_mkdir(*args, **kwargs) -> None:
        del args, kwargs
        raise OSError("simulated directory failure")

    monkeypatch.setattr("whisper_dictate.settings.Path.mkdir", fail_mkdir)

    with pytest.raises(SettingsWriteError):
        store.save(UserSettings())


def test_user_store_separates_normal_and_development_settings(tmp_path) -> None:
    environment = {"APPDATA": str(tmp_path / "roaming")}

    normal = SettingsStore.for_user(environment=environment)
    development = SettingsStore.for_user(
        development=True,
        environment=environment,
    )

    assert normal.path == tmp_path / "roaming" / "Bragi" / "settings.json"
    assert development.path == (
        tmp_path / "roaming" / "Bragi" / "development" / "settings.json"
    )
