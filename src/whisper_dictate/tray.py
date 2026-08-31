from __future__ import annotations

from collections.abc import Callable, Mapping


class TrayIcon:
    def __init__(
        self,
        on_exit: Callable[[], None],
        *,
        title: str = "Bragi",
        preview_actions: Mapping[str, Callable[[], None]] | None = None,
    ) -> None:
        self._on_exit = on_exit
        self._title = title
        self._preview_actions = dict(preview_actions or {})
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

        items = [
            pystray.MenuItem(self._title, None, enabled=False),
            pystray.Menu.SEPARATOR,
        ]
        if self._preview_actions:
            preview_items = [
                pystray.MenuItem(label, self._preview_clicked(action))
                for label, action in self._preview_actions.items()
            ]
            items.extend(
                [
                    pystray.MenuItem("Preview state", pystray.Menu(*preview_items)),
                    pystray.Menu.SEPARATOR,
                ]
            )
        items.append(pystray.MenuItem("Exit", self._exit_clicked))
        menu = pystray.Menu(*items)
        self._icon = pystray.Icon("bragi", self._image(), self._title, menu)
        self._icon.run_detached()

    @staticmethod
    def _preview_clicked(action: Callable[[], None]):
        def clicked(icon, item) -> None:
            del icon, item
            action()

        return clicked

    def _exit_clicked(self, icon, item) -> None:
        del item
        icon.stop()
        self._on_exit()

    def stop(self) -> None:
        if self._icon is not None:
            self._icon.stop()
            self._icon = None
