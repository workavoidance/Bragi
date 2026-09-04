from __future__ import annotations

import threading
from collections.abc import Callable

from whisper_dictate.i18n import tr

DEFAULT_HOTKEY = "right_ctrl"
CHORD_ACTIVATION_DELAY_SECONDS = 0.2
SUPPORTED_HOTKEYS = {
    "right_ctrl": "Right Ctrl",
    "left_ctrl_windows": "Left Ctrl + Windows",
    "left_ctrl_left_alt": "Left Ctrl + Left Alt",
    "f6": "F6",
    "f7": "F7",
    "f8": "F8",
    "f9": "F9",
    "f10": "F10",
    "f11": "F11",
    "f12": "F12",
}
HOTKEY_PARTS = {
    "right_ctrl": frozenset({"right_ctrl"}),
    "left_ctrl_windows": frozenset({"left_ctrl", "left_windows"}),
    "left_ctrl_left_alt": frozenset({"left_ctrl", "left_alt"}),
    **{f"f{number}": frozenset({f"f{number}"}) for number in range(6, 13)},
}


class HotkeyValidationError(ValueError):
    """Raised when a key is unsuitable for push-to-talk."""


class HotkeyActivationError(RuntimeError):
    """Raised when Windows cannot start the replacement listener."""


def validate_hotkey(identifier: str) -> str:
    if identifier not in SUPPORTED_HOTKEYS:
        raise HotkeyValidationError(
            tr(
                "Use Right Ctrl, Left Ctrl + Windows, Left Ctrl + Left Alt, "
                "or F6 through F12."
            )
        )
    return identifier


def hotkey_display_name(identifier: str) -> str:
    return SUPPORTED_HOTKEYS.get(identifier, tr("Unsupported key"))


def hotkey_identifier_for_parts(parts: set[str] | frozenset[str]) -> str | None:
    selected = frozenset(parts)
    for identifier, required in HOTKEY_PARTS.items():
        if selected == required:
            return identifier
    return None


def is_hotkey_part_prefix(parts: set[str] | frozenset[str]) -> bool:
    selected = frozenset(parts)
    return bool(selected) and any(
        selected < required for required in HOTKEY_PARTS.values()
    )


class HotkeyGesture:
    """Turn raw key transitions into one safe push-to-talk gesture."""

    def __init__(
        self,
        identifier: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
        on_cancel: Callable[[], None],
        *,
        timer_factory=threading.Timer,
    ) -> None:
        self.required = HOTKEY_PARTS[validate_hotkey(identifier)]
        self._on_press = on_press
        self._on_release = on_release
        self._on_cancel = on_cancel
        self._timer_factory = timer_factory
        self._down: set[str] = set()
        self._active = False
        self._blocked = False
        self._cancel_notified = False
        self._timer = None
        self._lock = threading.Lock()

    def press(self, part: str) -> None:
        if part == "escape":
            if len(self.required) > 1:
                with self._lock:
                    if self._down & self.required:
                        self._blocked = True
                        self._cancel_pending_locked()
            self._on_cancel()
            return

        activate_now = False
        cancel_now = False
        with self._lock:
            if part in self._down:
                return
            self._down.add(part)

            if len(self.required) == 1:
                if part in self.required and not self._active:
                    self._active = True
                    activate_now = True
            elif part not in self.required:
                if self._down & self.required:
                    self._blocked = True
                    self._cancel_pending_locked()
                    if self._active and not self._cancel_notified:
                        self._cancel_notified = True
                        cancel_now = True
            elif (
                self.required <= self._down
                and not self._blocked
                and not self._active
                and self._timer is None
                and not (self._down - self.required)
            ):
                timer = self._timer_factory(
                    CHORD_ACTIVATION_DELAY_SECONDS,
                    self._activate_chord,
                )
                if hasattr(timer, "daemon"):
                    timer.daemon = True
                self._timer = timer
                timer.start()
            elif self.required <= self._down and self._down - self.required:
                self._blocked = True

        if activate_now:
            self._on_press()
        if cancel_now:
            self._on_cancel()

    def release(self, part: str) -> None:
        release_now = False
        with self._lock:
            self._down.discard(part)
            if part not in self.required:
                return
            self._cancel_pending_locked()
            if self._active:
                self._active = False
                release_now = True
            if not (self._down & self.required):
                self._blocked = False
                self._cancel_notified = False

        if release_now:
            self._on_release()

    def close(self) -> None:
        with self._lock:
            self._cancel_pending_locked()
            self._down.clear()
            self._active = False
            self._blocked = False
            self._cancel_notified = False

    def _activate_chord(self) -> None:
        with self._lock:
            self._timer = None
            if (
                not self._active
                and not self._blocked
                and self.required <= self._down
                and not (self._down - self.required)
            ):
                self._active = True
                self._on_press()

    def _cancel_pending_locked(self) -> None:
        timer = self._timer
        self._timer = None
        if timer is not None:
            timer.cancel()


def _pynput_listener_factory(
    identifier: str,
    on_press: Callable[[], None],
    on_release: Callable[[], None],
    on_cancel: Callable[[], None],
):
    from pynput import keyboard

    key_parts = {
        keyboard.Key.ctrl_r: "right_ctrl",
        keyboard.Key.ctrl_l: "left_ctrl",
        keyboard.Key.cmd_l: "left_windows",
        keyboard.Key.alt_l: "left_alt",
        keyboard.Key.esc: "escape",
        **{
            getattr(keyboard.Key, f"f{number}"): f"f{number}" for number in range(6, 13)
        },
    }
    gesture = HotkeyGesture(identifier, on_press, on_release, on_cancel)

    def part_for(key) -> str:
        return key_parts.get(key, f"other:{key!r}")

    def pressed(key) -> None:
        gesture.press(part_for(key))

    def released(key) -> None:
        gesture.release(part_for(key))

    native_listener = keyboard.Listener(on_press=pressed, on_release=released)

    class GestureListener:
        def start(self) -> None:
            native_listener.start()

        def stop(self) -> None:
            gesture.close()
            native_listener.stop()

        def join(self, timeout=None) -> None:
            native_listener.join(timeout=timeout)

    return GestureListener()


class PushToTalkListener:
    """A replaceable global key listener with generation-safe callbacks."""

    def __init__(
        self,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
        hotkey: str = DEFAULT_HOTKEY,
        *,
        on_cancel: Callable[[], None] | None = None,
        listener_factory=None,
    ) -> None:
        self._on_press_callback = on_press
        self._on_release_callback = on_release
        self._on_cancel_callback = on_cancel or (lambda: None)
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
                self._on_cancel_callback,
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

    def stop(self, wait_timeout: float = 1.0) -> None:
        with self._lock:
            listener = self._listener
            self._listener = None
            self._generation += 1
            self._pressed = False
        if listener is not None:
            listener.stop()
            join = getattr(listener, "join", None)
            if callable(join) and listener is not threading.current_thread():
                try:
                    join(timeout=max(0.0, wait_timeout))
                except RuntimeError:
                    pass

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
                tr(
                    "That push-to-talk key could not be activated. The previous key "
                    "has been restored where possible."
                )
            ) from error


# Kept as a compatibility alias for integrations importing the prototype name.
RightControlListener = PushToTalkListener
