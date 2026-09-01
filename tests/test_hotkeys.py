from __future__ import annotations

import pytest

from whisper_dictate.hotkeys import (
    HotkeyActivationError,
    HotkeyValidationError,
    PushToTalkListener,
    validate_hotkey,
)


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


@pytest.mark.parametrize("identifier", ["a", "right_alt"])
def test_unsafe_push_to_talk_keys_are_rejected(identifier: str) -> None:
    with pytest.raises(HotkeyValidationError, match="not safe"):
        validate_hotkey(identifier)


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
