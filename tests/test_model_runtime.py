from __future__ import annotations

from pathlib import Path

import pytest

from whisper_dictate.model_runtime import ModelActivationError, ModelRuntime
from whisper_dictate.models import MODEL_BY_ID, ModelState
from whisper_dictate.settings import SettingsStore, UserSettings
from whisper_dictate.transcriber import LoadedModelSnapshot


class FakeManager:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.verified: list[str] = []

    def spec(self, identifier: str):
        return MODEL_BY_ID[identifier]

    def verify_installed(self, identifier: str, *, thorough: bool):
        assert thorough is True
        self.verified.append(identifier)
        return self.path / identifier


class FakeTranscriber:
    def __init__(self) -> None:
        self.active_model = "small"
        self.restored: LoadedModelSnapshot | None = None

    def switch_model(self, identifier: str, source: Path):
        assert source.name == identifier
        previous = LoadedModelSnapshot(self.active_model, object())
        self.active_model = identifier
        return previous

    def restore_model(self, snapshot: LoadedModelSnapshot) -> None:
        self.restored = snapshot
        self.active_model = snapshot.identifier


def test_model_activation_loads_before_persisting_and_reports_progress(
    tmp_path,
) -> None:
    store = SettingsStore(tmp_path / "settings.json")
    store.save(UserSettings())
    manager = FakeManager(tmp_path)
    transcriber = FakeTranscriber()
    synced = []
    runtime = ModelRuntime(
        manager,
        transcriber,
        store,
        settings_sync=synced.append,
    )
    events = []

    runtime.activate("base", events.append)

    assert manager.verified == ["base"]
    assert transcriber.active_model == "base"
    assert store.load().settings.model == "base"
    assert synced == [UserSettings(model="base")]
    assert [event.state for event in events] == [
        ModelState.LOADING,
        ModelState.INSTALLED,
    ]


def test_settings_failure_restores_the_previous_loaded_model(
    tmp_path, monkeypatch
) -> None:
    store = SettingsStore(tmp_path / "settings.json")
    store.save(UserSettings())
    transcriber = FakeTranscriber()
    runtime = ModelRuntime(FakeManager(tmp_path), transcriber, store)

    def fail_save(settings) -> None:
        del settings
        raise OSError("simulated failure")

    monkeypatch.setattr(store, "save", fail_save)

    with pytest.raises(OSError, match="simulated failure"):
        runtime.activate("base")

    assert transcriber.active_model == "small"
    assert transcriber.restored is not None


def test_model_change_waits_until_dictation_is_ready(tmp_path) -> None:
    store = SettingsStore(tmp_path / "settings.json")
    transcriber = FakeTranscriber()
    runtime = ModelRuntime(
        FakeManager(tmp_path),
        transcriber,
        store,
        can_activate=lambda: False,
    )

    with pytest.raises(ModelActivationError, match="Wait until Bragi is ready"):
        runtime.activate("base")

    assert transcriber.active_model == "small"
