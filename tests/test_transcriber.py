from __future__ import annotations

import threading
from types import SimpleNamespace

import numpy as np
import pytest

from whisper_dictate.config import AppConfig
from whisper_dictate.settings import LanguageMode
from whisper_dictate.transcriber import (
    LocalWhisperTranscriber,
    language_options,
    restricted_language,
)


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (LanguageMode.AUTOMATIC, None),
        (LanguageMode.NORWEGIAN, "no"),
        (LanguageMode.ENGLISH, "en"),
    ],
)
def test_language_options(mode, expected) -> None:
    assert language_options(mode) == expected


def test_restricted_language_ignores_unsupported_languages() -> None:
    assert restricted_language([("de", 0.72), ("en", 0.18), ("no", 0.10)]) == (
        "en",
        0.18,
    )


def test_restricted_language_prefers_norwegian_when_scores_are_equal() -> None:
    assert restricted_language([("en", 0.4), ("no", 0.4)]) == ("no", 0.4)


def test_automatic_detection_forces_the_best_norwegian_or_english_score(
    tmp_path,
) -> None:
    calls: list[dict[str, object]] = []

    class FakeModel:
        def detect_language(self, *, audio):
            assert audio.shape == (16_000,)
            return "de", 0.72, [("de", 0.72), ("en", 0.18), ("no", 0.10)]

        def transcribe(self, audio, **options):
            del audio
            calls.append(options)
            return [SimpleNamespace(text=" Hello")], SimpleNamespace(
                language="en", language_probability=1.0
            )

    transcriber = LocalWhisperTranscriber(AppConfig(), tmp_path)
    transcriber._model = FakeModel()

    result = transcriber.transcribe(np.ones(16_000, dtype=np.float32))

    assert result.text == "Hello"
    assert result.detected_language == "en"
    assert result.language_probability == 0.18
    assert calls[0]["language"] == "en"
    assert calls[0]["multilingual"] is False


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
