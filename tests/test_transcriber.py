from __future__ import annotations

import threading
from types import SimpleNamespace

import numpy as np
import pytest

from whisper_dictate.config import AppConfig
from whisper_dictate.settings import LanguageMode
from whisper_dictate.transcriber import LocalWhisperTranscriber, language_options


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (LanguageMode.AUTOMATIC, (None, False)),
        (LanguageMode.ENGLISH, ("en", False)),
        (LanguageMode.NORWEGIAN, ("no", False)),
        (LanguageMode.MULTILINGUAL, (None, True)),
    ],
)
def test_language_options(mode, expected) -> None:
    assert language_options(mode) == expected


def test_language_change_applies_to_the_next_recording(tmp_path) -> None:
    calls: list[dict[str, object]] = []

    class FakeModel:
        def transcribe(self, audio, **options):
            del audio
            calls.append(options)
            return [SimpleNamespace(text=" Hei æøå")], SimpleNamespace(
                language="no", language_probability=0.99
            )

    transcriber = LocalWhisperTranscriber(AppConfig(), tmp_path)
    transcriber._model = FakeModel()
    transcriber.set_language_mode(LanguageMode.NORWEGIAN)

    result = transcriber.transcribe(np.ones(16_000, dtype=np.float32))

    assert result.text == "Hei æøå"
    assert calls[0]["language"] == "no"
    assert calls[0]["multilingual"] is False


def test_model_switch_loads_candidate_before_replacing_working_model(tmp_path) -> None:
    transcriber = LocalWhisperTranscriber(AppConfig(), tmp_path)
    original = object()
    replacement = object()
    transcriber._model = original
    transcriber._create_model = lambda source: replacement

    snapshot = transcriber.switch_model("base", tmp_path / "installed" / "base")

    assert snapshot.identifier == "small"
    assert snapshot.model is original
    assert transcriber.active_model == "base"
    assert transcriber._model is replacement

    transcriber.restore_model(snapshot)
    assert transcriber.active_model == "small"
    assert transcriber._model is original


def test_cancelled_transcription_does_not_start_or_return_text(tmp_path) -> None:
    class ModelThatMustNotRun:
        def transcribe(self, audio, **options):
            raise AssertionError("cancelled transcription reached the model")

    transcriber = LocalWhisperTranscriber(AppConfig(), tmp_path)
    transcriber._model = ModelThatMustNotRun()
    cancelled = threading.Event()
    cancelled.set()

    result = transcriber.transcribe(
        np.ones(16_000, dtype=np.float32),
        cancel_event=cancelled,
    )

    assert result.text == ""
