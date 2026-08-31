from __future__ import annotations

from collections.abc import Callable


class TrayIcon:
    def __init__(self, on_exit: Callable[[], None]) -> None:
        self._on_exit = on_exit
        self._icon = None

    @staticmethod
    def _image():
        from PIL import Image, ImageDraw

        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((4, 4, 60, 60), fill="#1d4ed8")
        draw.rounded_rectangle((24, 13, 40, 39), radius=8, fill="white")
        draw.arc((18, 24, 46, 48), 0, 180, fill="white", width=4)
        draw.line((32, 46, 32, 53), fill="white", width=4)
        draw.line((24, 53, 40, 53), fill="white", width=4)
        return image

    def start(self) -> None:
        import pystray

        menu = pystray.Menu(
            pystray.MenuItem("Whisper Dictate", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._exit_clicked),
        )
        self._icon = pystray.Icon(
            "whisper_dictate", self._image(), "Whisper Dictate", menu
        )
        self._icon.run_detached()

    def _exit_clicked(self, icon, item) -> None:
        del item
        icon.stop()
        self._on_exit()

    def stop(self) -> None:
        if self._icon is not None:
            self._icon.stop()
            self._icon = None
