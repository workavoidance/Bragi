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

    assert path == tmp_path / "local" / "Bragi" / "models"
    assert path.is_dir()


def test_development_settings_are_separate(tmp_path) -> None:
    environment = {"APPDATA": str(tmp_path / "roaming")}

    normal = settings_directory(environment=environment)
    development = settings_directory(development=True, environment=environment)

    assert normal == tmp_path / "roaming" / "Bragi"
    assert development == normal / "development"
    assert normal != development


def test_explicit_development_build_identity() -> None:
    identity = detect_build_identity(
        environment={"BRAGI_DEVELOPMENT": "1", "BRAGI_BUILD_ID": "abc1234"}
    )

    assert identity == BuildIdentity(identifier="abc1234", development=True)
    assert identity.title == "Bragi DEV abc1234"


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
