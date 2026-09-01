from __future__ import annotations

import threading
from collections.abc import Callable

DEFAULT_HOTKEY = "right_ctrl"
SUPPORTED_HOTKEYS = {
    "right_ctrl": "Right Ctrl",
    "f6": "F6",
    "f7": "F7",
    "f8": "F8",
    "f9": "F9",
    "f10": "F10",
    "f11": "F11",
    "f12": "F12",
}


class HotkeyValidationError(ValueError):
    """Raised when a key is unsuitable for push-to-talk."""


class HotkeyActivationError(RuntimeError):
    """Raised when Windows cannot start the replacement listener."""


def validate_hotkey(identifier: str) -> str:
    if identifier not in SUPPORTED_HOTKEYS:
        raise HotkeyValidationError(
            "Use Right Ctrl or F6 through F12. Letters, Windows "
            "keys, and common editing keys are not safe push-to-talk choices."
        )
    return identifier


def hotkey_display_name(identifier: str) -> str:
    return SUPPORTED_HOTKEYS.get(identifier, "Unsupported key")


def _pynput_listener_factory(
    identifier: str,
    on_press: Callable[[], None],
    on_release: Callable[[], None],
):
    from pynput import keyboard

    key_names = {
        "right_ctrl": "ctrl_r",
        **{f"f{number}": f"f{number}" for number in range(6, 13)},
    }
    expected = getattr(keyboard.Key, key_names[identifier])

    def pressed(key) -> None:
        if key == expected:
            on_press()

    def released(key) -> None:
        if key == expected:
            on_release()

    return keyboard.Listener(on_press=pressed, on_release=released)


class PushToTalkListener:
    """A replaceable global key listener with generation-safe callbacks."""

    def __init__(
        self,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
        hotkey: str = DEFAULT_HOTKEY,
        *,
        listener_factory=None,
    ) -> None:
        self._on_press_callback = on_press
        self._on_release_callback = on_release
        self._hotkey = validate_hotkey(hotkey)
        self._pressed = False
        self._lock = threading.Lock()
        self._listener = None
        self._generation = 0
        self._listener_factory = listener_factory or _pynput_listener_factory

    @property
    def hotkey(self) -> str:
        with self._lock:
            return self._hotkey

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._listener is not None

    def _pressed_event(self, generation: int) -> None:
        with self._lock:
            if generation != self._generation or self._pressed:
                return
            self._pressed = True
        self._on_press_callback()

    def _released_event(self, generation: int) -> None:
        with self._lock:
            if generation != self._generation or not self._pressed:
                return
            self._pressed = False
        self._on_release_callback()

    def start(self) -> None:
        with self._lock:
            if self._listener is not None:
                return
            self._generation += 1
            generation = self._generation
            hotkey = self._hotkey
            listener = self._listener_factory(
                hotkey,
                lambda: self._pressed_event(generation),
                lambda: self._released_event(generation),
            )
            self._listener = listener
        try:
            listener.start()
        except Exception:
            with self._lock:
                if self._listener is listener:
                    self._listener = None
                    self._generation += 1
            raise

    def stop(self) -> None:
        with self._lock:
            listener = self._listener
            self._listener = None
            self._generation += 1
            self._pressed = False
        if listener is not None:
            listener.stop()

    def replace_hotkey(self, identifier: str) -> None:
        replacement = validate_hotkey(identifier)
        with self._lock:
            previous = self._hotkey
            was_active = self._listener is not None
        if replacement == previous:
            return
        if not was_active:
            with self._lock:
                self._hotkey = replacement
            return

        # Invalidate and stop the old generation before starting the new one.
        # Even if pynput finishes stopping asynchronously, its callbacks are ignored.
        self.stop()
        with self._lock:
            self._hotkey = replacement
        try:
            self.start()
        except Exception as error:
            with self._lock:
                self._hotkey = previous
            try:
                self.start()
            except Exception:
                pass
            raise HotkeyActivationError(
                "That push-to-talk key could not be activated. The previous key "
                "has been restored where possible."
            ) from error


# Kept as a compatibility alias for integrations importing the prototype name.
RightControlListener = PushToTalkListener
