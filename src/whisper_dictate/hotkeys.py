from __future__ import annotations

import threading
from collections.abc import Callable


class RightControlListener:
    def __init__(self, on_press: Callable[[], None], on_release: Callable[[], None]):
        self._on_press_callback = on_press
        self._on_release_callback = on_release
        self._pressed = False
        self._lock = threading.Lock()
        self._listener = None

    def start(self) -> None:
        from pynput import keyboard

        def on_press(key) -> None:
            if key != keyboard.Key.ctrl_r:
                return
            with self._lock:
                if self._pressed:
                    return
                self._pressed = True
            self._on_press_callback()

        def on_release(key) -> None:
            if key != keyboard.Key.ctrl_r:
                return
            with self._lock:
                if not self._pressed:
                    return
                self._pressed = False
            self._on_release_callback()

        self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
