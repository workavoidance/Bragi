from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

ULONG_PTR = (
    ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong
)


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]


class WindowsTextInjector:
    """Type Unicode directly with SendInput, leaving the clipboard untouched."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise OSError("WindowsTextInjector is available only on Windows")
        self._send_input = ctypes.windll.user32.SendInput
        self._send_input.argtypes = (
            wintypes.UINT,
            ctypes.POINTER(INPUT),
            ctypes.c_int,
        )
        self._send_input.restype = wintypes.UINT

    @staticmethod
    def _utf16_units(text: str) -> list[int]:
        encoded = text.encode("utf-16-le")
        return [
            int.from_bytes(encoded[index : index + 2], "little")
            for index in range(0, len(encoded), 2)
        ]

    @staticmethod
    def _event(unit: int, key_up: bool) -> INPUT:
        flags = KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if key_up else 0)
        return INPUT(
            type=INPUT_KEYBOARD,
            ki=KEYBDINPUT(
                wVk=0,
                wScan=unit,
                dwFlags=flags,
                time=0,
                dwExtraInfo=0,
            ),
        )

    def type_text(self, text: str) -> None:
        units = self._utf16_units(text)
        # Sending moderate batches avoids oversized stack allocations on long
        # dictations while still inserting the result quickly.
        for start in range(0, len(units), 120):
            batch_units = units[start : start + 120]
            events = []
            for unit in batch_units:
                events.append(self._event(unit, key_up=False))
                events.append(self._event(unit, key_up=True))
            array_type = INPUT * len(events)
            array = array_type(*events)
            sent = self._send_input(len(events), array, ctypes.sizeof(INPUT))
            if sent != len(events):
                raise ctypes.WinError(ctypes.get_last_error())
