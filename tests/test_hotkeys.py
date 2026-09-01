from __future__ import annotations

import pytest

from whisper_dictate.hotkeys import (
    HotkeyActivationError,
    HotkeyValidationError,
    PushToTalkListener,
    validate_hotkey,
)


class FakeNativeListener:
    def __init__(self, identifier, on_press, on_release, events, fail=False) -> None:
        self.identifier = identifier
        self.on_press = on_press
        self.on_release = on_release
        self.events = events
        self.fail = fail

    def start(self) -> None:
        self.events.append(f"start:{self.identifier}")
        if self.fail:
            raise RuntimeError("simulated conflict")

    def stop(self) -> None:
        self.events.append(f"stop:{self.identifier}")


def test_unsafe_push_to_talk_keys_are_rejected() -> None:
    with pytest.raises(HotkeyValidationError, match="not safe"):
        validate_hotkey("a")


def test_hotkey_replacement_stops_old_listener_and_ignores_old_callbacks() -> None:
    events: list[str] = []
    listeners: list[FakeNativeListener] = []

    def factory(identifier, on_press, on_release):
        listener = FakeNativeListener(identifier, on_press, on_release, events)
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

    def factory(identifier, on_press, on_release):
        return FakeNativeListener(
            identifier,
            on_press,
            on_release,
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
