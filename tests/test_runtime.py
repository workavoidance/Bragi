from __future__ import annotations

import json

from whisper_dictate.runtime import (
    BuildIdentity,
    detect_build_identity,
    model_cache_directory,
    settings_directory,
)


def test_model_cache_uses_stable_local_app_data(tmp_path) -> None:
    environment = {"LOCALAPPDATA": str(tmp_path / "local")}

    path = model_cache_directory(environment=environment)

    assert path == tmp_path / "local" / "Skrivi" / "models"
    assert path.is_dir()


def test_existing_bragi_models_move_to_skrivi_without_copying(tmp_path) -> None:
    environment = {"LOCALAPPDATA": str(tmp_path / "local")}
    legacy_model = (
        tmp_path / "local" / "Bragi" / "models" / "installed" / "small" / "model.bin"
    )
    legacy_model.parent.mkdir(parents=True)
    legacy_model.write_bytes(b"existing model weights")

    path = model_cache_directory(environment=environment)

    assert path == tmp_path / "local" / "Skrivi" / "models"
    assert (path / "installed" / "small" / "model.bin").read_bytes() == (
        b"existing model weights"
    )
    assert not (tmp_path / "local" / "Bragi").exists()


def test_existing_bragi_settings_move_to_skrivi(tmp_path) -> None:
    environment = {"APPDATA": str(tmp_path / "roaming")}
    legacy_settings = tmp_path / "roaming" / "Bragi" / "development" / "settings.json"
    legacy_settings.parent.mkdir(parents=True)
    legacy_settings.write_text('{"existing": true}', encoding="utf-8")

    path = settings_directory(development=True, environment=environment)

    assert path == tmp_path / "roaming" / "Skrivi" / "development"
    assert (path / "settings.json").read_text(encoding="utf-8") == (
        '{"existing": true}'
    )
    assert not (tmp_path / "roaming" / "Bragi").exists()


def test_failed_directory_rename_keeps_using_existing_bragi_data(
    tmp_path, monkeypatch
) -> None:
    environment = {"APPDATA": str(tmp_path / "roaming")}
    legacy_settings = tmp_path / "roaming" / "Bragi" / "settings.json"
    legacy_settings.parent.mkdir(parents=True)
    legacy_settings.write_text("existing settings", encoding="utf-8")

    def fail_replace(source, destination) -> None:
        del source, destination
        raise OSError("simulated directory lock")

    monkeypatch.setattr("whisper_dictate.runtime.os.replace", fail_replace)

    path = settings_directory(environment=environment)

    assert path == tmp_path / "roaming" / "Bragi"
    assert (path / "settings.json").read_text(encoding="utf-8") == ("existing settings")


def test_development_settings_are_separate(tmp_path) -> None:
    environment = {"APPDATA": str(tmp_path / "roaming")}

    normal = settings_directory(environment=environment)
    development = settings_directory(development=True, environment=environment)

    assert normal == tmp_path / "roaming" / "Skrivi"
    assert development == normal / "development"
    assert normal != development


def test_explicit_development_build_identity() -> None:
    identity = detect_build_identity(
        environment={"SKRIVI_DEVELOPMENT": "1", "SKRIVI_BUILD_ID": "abc1234"}
    )

    assert identity == BuildIdentity(identifier="abc1234", development=True)
    assert identity.title == "Skrivi DEV abc1234"


def test_packaged_preview_identity(tmp_path) -> None:
    (tmp_path / "BUILD_INFO.json").write_text(
        json.dumps({"build_id": "PR-11-abc1234", "development": True}),
        encoding="utf-8",
    )

    identity = detect_build_identity(environment={}, executable_directory=tmp_path)

    assert identity == BuildIdentity(identifier="PR-11-abc1234", development=True)


def test_invalid_packaged_identity_falls_back(tmp_path) -> None:
    (tmp_path / "BUILD_INFO.json").write_text("not json", encoding="utf-8")

    identity = detect_build_identity(environment={}, executable_directory=tmp_path)

    assert identity.development is False
    assert identity.identifier
