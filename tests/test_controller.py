from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from whisper_dictate.audio import CapturedAudio
from whisper_dictate.config import AppConfig
from whisper_dictate.controller import AppState, DictationController


class FakeRecorder:
    is_recording = False


class FakeHotkey:
    def stop(self) -> None:
        pass


class FakeIndicator:
    def __init__(self) -> None:
        self.events: list[tuple[str, str | None]] = []

    def post(self, state: str, detail: str | None = None) -> None:
        self.events.append((state, detail))


class FakeInjector:
    def __init__(self) -> None:
        self.typed: list[str] = []

    def type_text(self, text: str) -> None:
        self.typed.append(text)


@dataclass
class FakeResult:
    text: str


class FakeTranscriber:
    def __init__(self, text: str) -> None:
        self.text = text

    def transcribe(self, audio: np.ndarray) -> FakeResult:
        assert audio.dtype == np.float32
        return FakeResult(self.text)


def make_controller(text: str = "Hei, this is local."):
    indicator = FakeIndicator()
    injector = FakeInjector()
    config = AppConfig(injection_delay_seconds=0.0)
    controller = DictationController(
        config=config,
        recorder=FakeRecorder(),
        transcriber=FakeTranscriber(text),
        injector=injector,
        indicator=indicator,
        hotkey_listener=FakeHotkey(),
    )
    controller._set_state(AppState.TRANSCRIBING)
    return controller, indicator, injector


def test_completed_dictation_is_typed_and_audio_is_cleared() -> None:
    controller, indicator, injector = make_controller()
    samples = np.full(48_000, 0.1, dtype=np.float32)
    captured = CapturedAudio(samples=samples, sample_rate=48_000)

    controller._process_recording(captured)

    assert injector.typed == ["Hei, this is local."]
    assert ("ready", None) in indicator.events
    assert controller.state is AppState.READY
    assert np.count_nonzero(samples) == 0


def test_silent_dictation_is_not_typed() -> None:
    controller, indicator, injector = make_controller()
    samples = np.zeros(48_000, dtype=np.float32)

    controller._process_recording(CapturedAudio(samples=samples, sample_rate=48_000))

    assert injector.typed == []
    assert ("empty", None) in indicator.events
    assert controller.state is AppState.READY
