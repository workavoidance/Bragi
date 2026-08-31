from __future__ import annotations

import ctypes
import os
import queue
import tkinter as tk
from collections.abc import Callable


class FloatingIndicator:
    WIDTH = 290
    HEIGHT = 58

    THEMES = {
        "loading": ("#334155", "Preparing local speech model…"),
        "ready": ("#15803d", "Ready — hold Right Ctrl to dictate"),
        "recording": ("#b91c1c", "●  Listening — release Right Ctrl"),
        "transcribing": ("#1d4ed8", "Transcribing locally…"),
        "empty": ("#92400e", "No speech detected"),
        "error": ("#9a3412", "Something went wrong"),
    }

    def __init__(self, title: str = "Bragi") -> None:
        self.root = tk.Tk()
        self.root.title(title)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#0f172a")
        self.root.withdraw()

        self.label = tk.Label(
            self.root,
            text="",
            fg="white",
            bg="#334155",
            font=("Segoe UI", 11, "bold"),
            padx=18,
            pady=16,
        )
        self.label.pack(fill="both", expand=True)
        self._events: queue.SimpleQueue[tuple[str, str | None]] = queue.SimpleQueue()
        self._hide_job = None
        self._exit_handler: Callable[[], None] | None = None
        self.root.protocol("WM_DELETE_WINDOW", self.request_exit)
        self.root.after(30, self._poll)

    def set_exit_handler(self, handler: Callable[[], None]) -> None:
        self._exit_handler = handler

    def post(self, state: str, detail: str | None = None) -> None:
        self._events.put((state, detail))

    def request_exit(self) -> None:
        self._events.put(("exit", None))

    def _poll(self) -> None:
        try:
            while True:
                state, detail = self._events.get_nowait()
                if state == "exit":
                    if self._exit_handler:
                        self._exit_handler()
                    self.root.quit()
                    return
                self._render(state, detail)
        except queue.Empty:
            pass
        self.root.after(30, self._poll)

    def _render(self, state: str, detail: str | None) -> None:
        color, default_text = self.THEMES.get(state, self.THEMES["error"])
        text = detail or default_text
        self.label.configure(text=text, bg=color)
        self.root.configure(bg=color)
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max(0, (screen_width - self.WIDTH) // 2)
        y = max(0, screen_height - self.HEIGHT - 92)
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
        self._show_without_activation()

        if self._hide_job is not None:
            self.root.after_cancel(self._hide_job)
            self._hide_job = None
        delay = {
            "ready": 1400,
            "empty": 1800,
            "error": 6000,
        }.get(state)
        if delay:
            self._hide_job = self.root.after(delay, self.root.withdraw)

    def _show_without_activation(self) -> None:
        self.root.deiconify()
        if os.name != "nt":
            return
        self.root.update_idletasks()
        user32 = ctypes.windll.user32
        user32.GetParent.argtypes = (ctypes.c_void_p,)
        user32.GetParent.restype = ctypes.c_void_p
        hwnd = user32.GetParent(self.root.winfo_id())
        if not hwnd:
            hwnd = self.root.winfo_id()
        gwl_exstyle = -20
        ws_ex_toolwindow = 0x00000080
        ws_ex_noactivate = 0x08000000
        style = user32.GetWindowLongW(hwnd, gwl_exstyle)
        user32.SetWindowLongW(
            hwnd, gwl_exstyle, style | ws_ex_toolwindow | ws_ex_noactivate
        )
        sw_shownoactivate = 4
        user32.ShowWindow(hwnd, sw_shownoactivate)

    def run(self) -> None:
        self.root.mainloop()
        self.root.destroy()
