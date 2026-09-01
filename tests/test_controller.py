from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import numpy as np

from whisper_dictate.audio import CapturedAudio, MicrophoneUnavailableError
from whisper_dictate.config import AppConfig
from whisper_dictate.controller import AppState, DictationController
from whisper_dictate.settings import LanguageMode


class FakeRecorder:
    def __init__(self) -> None:
        self.is_recording = False
        self.cancel_count = 0

    def start(self) -> None:
        self.is_recording = True

    def stop(self) -> CapturedAudio:
        self.is_recording = False
        return CapturedAudio(np.full(48_000, 0.1, dtype=np.float32), 48_000)

    def cancel(self) -> None:
        self.is_recording = False
        self.cancel_count += 1


class FakeHotkey:
    def start(self) -> None:
        pass

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

    def transcribe(
        self,
        audio: np.ndarray,
        *,
        cancel_event: threading.Event | None = None,
    ) -> FakeResult:
        assert audio.dtype == np.float32
        if cancel_event is not None and cancel_event.is_set():
            return FakeResult("")
        return FakeResult(self.text)

    language_mode = LanguageMode.AUTOMATIC


class FakeTimer:
    def __init__(self, interval: float, callback) -> None:
        self.interval = interval
        self.callback = callback
        self.started = False
        self.cancelled = False
        self.daemon = False

    def start(self) -> None:
        self.started = True

    def cancel(self) -> None:
        self.cancelled = True

    def fire(self) -> None:
        self.callback()


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


def test_very_short_automatic_recording_explains_detection_limit() -> None:
    controller, indicator, injector = make_controller()
    samples = np.full(1_000, 0.1, dtype=np.float32)

    controller._process_recording(CapturedAudio(samples=samples, sample_rate=48_000))

    assert injector.typed == []
    assert indicator.events[-1] == (
        "empty",
        "Phrase too short. Automatic language detection works better with a "
        "longer phrase.",
    )


def test_disconnected_microphone_error_is_shown_without_entering_recording() -> None:
    class MissingRecorder(FakeRecorder):
        def start(self) -> None:
            raise MicrophoneUnavailableError(
                "The selected microphone is unavailable. Choose Windows Default."
            )

    indicator = FakeIndicator()
    controller = DictationController(
        config=AppConfig(),
        recorder=MissingRecorder(),
        transcriber=FakeTranscriber(""),
        injector=FakeInjector(),
        indicator=indicator,
        hotkey_listener=FakeHotkey(),
    )
    controller._set_state(AppState.READY)

    controller.on_hotkey_press()

    assert controller.state is AppState.READY
    assert indicator.events == [
        (
            "error",
            "The selected microphone is unavailable. Choose Windows Default.",
        )
    ]


def test_model_loading_does_not_block_the_calling_thread() -> None:
    started = threading.Event()
    release = threading.Event()

    class BlockingTranscriber(FakeTranscriber):
        def load(self) -> None:
            started.set()
            release.wait(timeout=1.0)

    controller = DictationController(
        config=AppConfig(),
        recorder=FakeRecorder(),
        transcriber=BlockingTranscriber(""),
        injector=FakeInjector(),
        indicator=FakeIndicator(),
        hotkey_listener=FakeHotkey(),
    )

    before = time.monotonic()
    controller.start()
    elapsed = time.monotonic() - before

    assert elapsed < 0.2
    assert started.wait(timeout=0.5)
    assert controller.state is AppState.LOADING
    release.set()
    controller.stop()


def test_escape_cancels_recording_without_transcribing() -> None:
    recorder = FakeRecorder()
    indicator = FakeIndicator()
    transcriber = FakeTranscriber("This must not be typed")
    injector = FakeInjector()
    controller = DictationController(
        config=AppConfig(),
        recorder=recorder,
        transcriber=transcriber,
        injector=injector,
        indicator=indicator,
        hotkey_listener=FakeHotkey(),
    )
    controller._set_state(AppState.READY)

    controller.on_hotkey_press()
    controller.cancel_current()
    controller.on_hotkey_release()

    assert recorder.cancel_count == 1
    assert injector.typed == []
    assert controller.state is AppState.READY
    assert indicator.events[-1] == ("cancelled", "Dictation cancelled")


def test_recording_limit_discards_audio_and_returns_to_ready() -> None:
    timers: list[FakeTimer] = []

    def timer_factory(interval, callback):
        timer = FakeTimer(interval, callback)
        timers.append(timer)
        return timer

    recorder = FakeRecorder()
    indicator = FakeIndicator()
    controller = DictationController(
        config=AppConfig(max_recording_seconds=300.0),
        recorder=recorder,
        transcriber=FakeTranscriber("This must not be typed"),
        injector=FakeInjector(),
        indicator=indicator,
        hotkey_listener=FakeHotkey(),
        timer_factory=timer_factory,
    )
    controller._set_state(AppState.READY)

    controller.on_hotkey_press()
    timers[0].fire()

    assert timers[0].interval == 300.0
    assert recorder.cancel_count == 1
    assert controller.state is AppState.READY
    assert indicator.events[-1] == (
        "cancelled",
        "Recording cancelled after 5 minutes. Hold the key again to start over.",
    )


def test_expired_recording_timer_cannot_cancel_transcription() -> None:
    controller, _indicator, injector = make_controller("Keep this text")
    samples = np.full(48_000, 0.1, dtype=np.float32)

    controller._recording_limit_reached()
    controller._process_recording(CapturedAudio(samples=samples, sample_rate=48_000))

    assert injector.typed == ["Keep this text"]


def test_cancelling_transcription_prevents_text_insertion_and_clears_audio() -> None:
    controller, indicator, injector = make_controller("This must not be typed")
    samples = np.full(48_000, 0.1, dtype=np.float32)

    controller.cancel_current()
    controller._process_recording(CapturedAudio(samples=samples, sample_rate=48_000))

    assert injector.typed == []
    assert np.count_nonzero(samples) == 0
    assert controller.state is AppState.READY
    assert indicator.events[-1] == ("cancelled", "Dictation cancelled")
