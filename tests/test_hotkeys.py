from __future__ import annotations

import pytest

from whisper_dictate.hotkeys import (
    CHORD_ACTIVATION_DELAY_SECONDS,
    HotkeyActivationError,
    HotkeyGesture,
    HotkeyValidationError,
    PushToTalkListener,
    validate_hotkey,
)


class FakeTimer:
    def __init__(self, delay, callback, timers) -> None:
        self.delay = delay
        self.callback = callback
        self.timers = timers
        self.cancelled = False
        self.daemon = False

    def start(self) -> None:
        self.timers.append(self)

    def cancel(self) -> None:
        self.cancelled = True

    def fire(self) -> None:
        if not self.cancelled:
            self.callback()


class FakeNativeListener:
    def __init__(
        self, identifier, on_press, on_release, on_cancel, events, fail=False
    ) -> None:
        self.identifier = identifier
        self.on_press = on_press
        self.on_release = on_release
        self.on_cancel = on_cancel
        self.events = events
        self.fail = fail

    def start(self) -> None:
        self.events.append(f"start:{self.identifier}")
        if self.fail:
            raise RuntimeError("simulated conflict")

    def stop(self) -> None:
        self.events.append(f"stop:{self.identifier}")


@pytest.mark.parametrize("identifier", ["a", "right_alt", "left_windows"])
def test_unsafe_push_to_talk_keys_are_rejected(identifier: str) -> None:
    with pytest.raises(HotkeyValidationError, match="Use Right Ctrl"):
        validate_hotkey(identifier)


@pytest.mark.parametrize(
    "identifier", ["right_ctrl", "left_ctrl_windows", "left_ctrl_left_alt", "f8"]
)
def test_supported_single_keys_and_laptop_combinations_are_valid(
    identifier: str,
) -> None:
    assert validate_hotkey(identifier) == identifier


@pytest.mark.parametrize(
    ("identifier", "first", "second"),
    [
        ("left_ctrl_windows", "left_ctrl", "left_windows"),
        ("left_ctrl_windows", "left_windows", "left_ctrl"),
        ("left_ctrl_left_alt", "left_ctrl", "left_alt"),
        ("left_ctrl_left_alt", "left_alt", "left_ctrl"),
    ],
)
def test_laptop_chord_activates_after_a_short_hold_and_releases_with_either_key(
    identifier: str, first: str, second: str
) -> None:
    events: list[str] = []
    timers: list[FakeTimer] = []
    gesture = HotkeyGesture(
        identifier,
        lambda: events.append("press"),
        lambda: events.append("release"),
        lambda: events.append("cancel"),
        timer_factory=lambda delay, callback: FakeTimer(delay, callback, timers),
    )

    gesture.press(first)
    gesture.press(second)

    assert events == []
    assert len(timers) == 1
    assert timers[0].delay == CHORD_ACTIVATION_DELAY_SECONDS

    timers[0].fire()
    gesture.release(first)
    gesture.release(second)

    assert events == ["press", "release"]


def test_third_key_before_threshold_preserves_normal_windows_shortcut() -> None:
    events: list[str] = []
    timers: list[FakeTimer] = []
    gesture = HotkeyGesture(
        "left_ctrl_windows",
        lambda: events.append("press"),
        lambda: events.append("release"),
        lambda: events.append("cancel"),
        timer_factory=lambda delay, callback: FakeTimer(delay, callback, timers),
    )

    gesture.press("left_ctrl")
    gesture.press("left_windows")
    gesture.press("other:v")
    timers[0].fire()
    gesture.release("other:v")
    gesture.release("left_windows")
    gesture.release("left_ctrl")

    assert events == []
    assert timers[0].cancelled is True


def test_escape_cancels_a_pending_laptop_chord() -> None:
    events: list[str] = []
    timers: list[FakeTimer] = []
    gesture = HotkeyGesture(
        "left_ctrl_windows",
        lambda: events.append("press"),
        lambda: events.append("release"),
        lambda: events.append("cancel"),
        timer_factory=lambda delay, callback: FakeTimer(delay, callback, timers),
    )

    gesture.press("left_ctrl")
    gesture.press("left_windows")
    gesture.press("escape")
    timers[0].fire()

    assert events == ["cancel"]
    assert timers[0].cancelled is True


def test_third_key_cancels_an_active_laptop_chord_once() -> None:
    events: list[str] = []
    timers: list[FakeTimer] = []
    gesture = HotkeyGesture(
        "left_ctrl_windows",
        lambda: events.append("press"),
        lambda: events.append("release"),
        lambda: events.append("cancel"),
        timer_factory=lambda delay, callback: FakeTimer(delay, callback, timers),
    )

    gesture.press("left_ctrl")
    gesture.press("left_windows")
    timers[0].fire()
    gesture.press("other:v")
    gesture.press("other:b")
    gesture.release("left_windows")

    assert events == ["press", "cancel", "release"]


def test_single_key_hotkeys_remain_immediate() -> None:
    events: list[str] = []
    gesture = HotkeyGesture(
        "right_ctrl",
        lambda: events.append("press"),
        lambda: events.append("release"),
        lambda: events.append("cancel"),
    )

    gesture.press("right_ctrl")
    gesture.release("right_ctrl")

    assert events == ["press", "release"]


def test_hotkey_replacement_stops_old_listener_and_ignores_old_callbacks() -> None:
    events: list[str] = []
    listeners: list[FakeNativeListener] = []

    def factory(identifier, on_press, on_release, on_cancel):
        listener = FakeNativeListener(
            identifier, on_press, on_release, on_cancel, events
        )
        listeners.append(listener)
        return listener

    listener = PushToTalkListener(
        lambda: events.append("press"),
        lambda: events.append("release"),
        listener_factory=factory,
    )
    listener.start()
    old_listener = listeners[0]
    listener.replace_hotkey("f8")

    old_listener.on_press()
    listeners[1].on_press()
    listeners[1].on_press()
    listeners[1].on_release()

    assert events == [
        "start:right_ctrl",
        "stop:right_ctrl",
        "start:f8",
        "press",
        "release",
    ]
    assert listener.hotkey == "f8"
    assert listener.is_active is True


def test_failed_replacement_restores_previous_hotkey() -> None:
    events: list[str] = []

    def factory(identifier, on_press, on_release, on_cancel):
        return FakeNativeListener(
            identifier,
            on_press,
            on_release,
            on_cancel,
            events,
            fail=identifier == "f8",
        )

    listener = PushToTalkListener(
        lambda: None,
        lambda: None,
        listener_factory=factory,
    )
    listener.start()

    with pytest.raises(HotkeyActivationError, match="previous key"):
        listener.replace_hotkey("f8")

    assert listener.hotkey == "right_ctrl"
    assert listener.is_active is True
    assert events == [
        "start:right_ctrl",
        "stop:right_ctrl",
        "start:f8",
        "start:right_ctrl",
    ]


def test_escape_requests_cancellation_without_changing_key_state() -> None:
    events: list[str] = []
    listeners: list[FakeNativeListener] = []

    def factory(identifier, on_press, on_release, on_cancel):
        listener = FakeNativeListener(
            identifier, on_press, on_release, on_cancel, events
        )
        listeners.append(listener)
        return listener

    listener = PushToTalkListener(
        lambda: events.append("press"),
        lambda: events.append("release"),
        on_cancel=lambda: events.append("cancel"),
        listener_factory=factory,
    )
    listener.start()

    listeners[0].on_press()
    listeners[0].on_cancel()
    listeners[0].on_release()

    assert events == ["start:right_ctrl", "press", "cancel", "release"]


def test_stop_waits_briefly_for_native_listener_shutdown() -> None:
    events: list[str] = []

    class JoinableNativeListener(FakeNativeListener):
        def join(self, timeout=None) -> None:
            events.append(f"join:{timeout}")

    def factory(identifier, on_press, on_release, on_cancel):
        return JoinableNativeListener(
            identifier,
            on_press,
            on_release,
            on_cancel,
            events,
        )

    listener = PushToTalkListener(
        lambda: None,
        lambda: None,
        listener_factory=factory,
    )
    listener.start()

    listener.stop(wait_timeout=0.25)

    assert events == ["start:right_ctrl", "stop:right_ctrl", "join:0.25"]
