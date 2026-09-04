from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QCursor, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QWidget

from whisper_dictate.application import theme_colors
from whisper_dictate.hotkeys import DEFAULT_HOTKEY, hotkey_display_name, validate_hotkey
from whisper_dictate.i18n import add_interface_language_listener, tr


def overlay_position(
    screen: tuple[int, int, int, int],
    overlay: tuple[int, int],
    *,
    bottom_margin: int = 64,
) -> tuple[int, int]:
    """Place an overlay at the bottom-centre of one display's work area."""
    left, top, screen_width, screen_height = screen
    overlay_width, overlay_height = overlay
    x = left + max(0, (screen_width - overlay_width) // 2)
    y = top + max(0, screen_height - overlay_height - bottom_margin)
    return x, y


def indicator_stylesheet(
    palette: QPalette, *, high_contrast: bool | None = None
) -> str:
    colors = theme_colors(palette, high_contrast=high_contrast)
    return f"""
        QFrame#skriviStatusFrame {{
            background: {colors["surface"]};
            border: 1px solid {colors["control_border"]};
            border-radius: 16px;
        }}
        QLabel {{
            color: {colors["text"]};
            background: transparent;
        }}
        QLabel#skriviStateMark {{
            color: {colors["accent"]};
        }}
    """


class FloatingIndicator(QWidget):
    """Compact, non-activating status overlay safe to update from workers."""

    state_requested = Signal(str, object)
    exit_requested = Signal()
    status_changed = Signal(str, str)

    STATES = {
        "loading": ("…", "Preparing local speech model…"),
        "ready": ("✓", "Ready to dictate"),
        "recording": (
            "●",
            "Listening. Release your dictation key, or press Esc to cancel",
        ),
        "transcribing": ("↻", "Transcribing locally…"),
        "cancelled": ("×", "Dictation cancelled"),
        "empty": ("!", "No speech detected"),
        "model_error": ("!", "Speech model unavailable"),
        "error": ("!", "Something went wrong"),
    }
    HIDE_DELAYS_MS = {
        "ready": 1400,
        "cancelled": 1800,
        "empty": 1800,
        "model_error": 6000,
        "error": 6000,
    }

    def __init__(
        self,
        title: str = "Skrivi",
        *,
        enabled: bool = True,
        hotkey: str = DEFAULT_HOTKEY,
    ) -> None:
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("create_application() must be called before the UI")
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setWindowTitle(title)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAccessibleName(tr("Skrivi dictation status"))
        self.setAccessibleDescription(
            tr("Shows whether Skrivi is loading, listening, or transcribing.")
        )
        self.setMinimumWidth(300)
        self.setMaximumWidth(480)
        self._refresh_theme(app.palette())
        app.paletteChanged.connect(self._refresh_theme)

        self._enabled = enabled
        self._exit_handler: Callable[[], None] | None = None
        self._exiting = False
        self._current_state: str | None = None
        self._current_detail: str | None = None
        self._hotkey = validate_hotkey(hotkey)

        frame = QFrame(self)
        frame.setObjectName("skriviStatusFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 18, 12)
        layout.setSpacing(12)

        self._state_mark = QLabel("…", frame)
        self._state_mark.setObjectName("skriviStateMark")
        state_font = self._state_mark.font()
        state_font.setBold(True)
        state_font.setPointSize(max(state_font.pointSize() + 4, 14))
        self._state_mark.setFont(state_font)
        self._state_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._state_mark.setAccessibleName(tr("Status symbol"))
        layout.addWidget(self._state_mark)

        self._message = QLabel("", frame)
        message_font = self._message.font()
        message_font.setBold(True)
        self._message.setFont(message_font)
        self._message.setWordWrap(True)
        self._message.setAccessibleName(tr("Dictation status message"))
        layout.addWidget(self._message, 1)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)
        self.state_requested.connect(self._render)
        self.exit_requested.connect(self._exit)
        add_interface_language_listener(self.retranslate_ui)

    @Slot(QPalette)
    def _refresh_theme(self, palette: QPalette) -> None:
        self.setStyleSheet(indicator_stylesheet(palette))

    def set_exit_handler(self, handler: Callable[[], None]) -> None:
        self._exit_handler = handler

    def post(self, state: str, detail: str | None = None) -> None:
        self.state_requested.emit(state, detail)

    def request_exit(self) -> None:
        self.exit_requested.emit()

    @Slot(bool)
    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self._hide_timer.stop()
            self.hide()

    @Slot(str)
    def set_hotkey(self, identifier: str) -> None:
        self._hotkey = validate_hotkey(identifier)
        if self._current_state == "ready" and self._current_detail is None:
            self._update_text("ready", None)

    @Slot(str, object)
    def _render(self, state: str, detail: object) -> None:
        self._current_state = state
        self._current_detail = detail if isinstance(detail, str) and detail else None
        self._update_text(state, self._current_detail)

        self._hide_timer.stop()
        delay = self.HIDE_DELAYS_MS.get(state)
        if delay is not None:
            self._hide_timer.start(delay)
        if not self._enabled:
            return

        self.adjustSize()
        screen = QGuiApplication.screenAt(QCursor.pos())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            x, y = overlay_position(
                (available.x(), available.y(), available.width(), available.height()),
                (self.width(), self.height()),
            )
            self.move(x, y)
        self.show()
        self.raise_()

    def _update_text(self, state: str, detail: str | None) -> None:
        symbol, default_text = self.STATES.get(state, self.STATES["error"])
        if state == "ready" and detail is None:
            text = tr(
                "Ready. Hold {hotkey} to dictate",
                hotkey=tr(hotkey_display_name(self._hotkey)),
            )
        else:
            text = tr(detail or default_text)
        self._state_mark.setText(symbol)
        self._state_mark.setAccessibleDescription(text)
        self._message.setText(text)
        self.status_changed.emit(state, text)

    def retranslate_ui(self) -> None:
        self.setAccessibleName(tr("Skrivi dictation status"))
        self.setAccessibleDescription(
            tr("Shows whether Skrivi is loading, listening, or transcribing.")
        )
        self._state_mark.setAccessibleName(tr("Status symbol"))
        self._message.setAccessibleName(tr("Dictation status message"))
        if self._current_state is not None:
            self._update_text(self._current_state, self._current_detail)

    @Slot()
    def _exit(self) -> None:
        if self._exiting:
            return
        self._exiting = True
        self._hide_timer.stop()
        self.hide()
        try:
            if self._exit_handler is not None:
                self._exit_handler()
        finally:
            app = QApplication.instance()
            if app is not None:
                app.quit()

    def run(self) -> int:
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("The Qt application is not available")
        return app.exec()
