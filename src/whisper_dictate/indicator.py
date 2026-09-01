from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QWidget


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


class FloatingIndicator(QWidget):
    """Compact, non-activating status overlay safe to update from workers."""

    state_requested = Signal(str, object)
    exit_requested = Signal()
    status_changed = Signal(str, str)

    STATES = {
        "loading": ("…", "Preparing local speech model…"),
        "ready": ("✓", "Ready. Hold Right Ctrl to dictate"),
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

    def __init__(self, title: str = "Bragi", *, enabled: bool = True) -> None:
        if QApplication.instance() is None:
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
        self.setAccessibleName("Bragi dictation status")
        self.setAccessibleDescription(
            "Shows whether Bragi is loading, listening, or transcribing."
        )
        self.setMinimumWidth(300)
        self.setMaximumWidth(480)
        self.setStyleSheet(
            """
            QFrame#bragiStatusFrame {
                background: #FFFDF9;
                border: 1px solid #DED7CF;
                border-radius: 16px;
            }
            QLabel {
                color: #181817;
                background: transparent;
            }
            QLabel#bragiStateMark {
                color: #F05A24;
            }
            """
        )

        self._enabled = enabled
        self._exit_handler: Callable[[], None] | None = None
        self._exiting = False

        frame = QFrame(self)
        frame.setObjectName("bragiStatusFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 18, 12)
        layout.setSpacing(12)

        self._state_mark = QLabel("…", frame)
        self._state_mark.setObjectName("bragiStateMark")
        state_font = self._state_mark.font()
        state_font.setBold(True)
        state_font.setPointSize(max(state_font.pointSize() + 4, 14))
        self._state_mark.setFont(state_font)
        self._state_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._state_mark.setAccessibleName("Status symbol")
        layout.addWidget(self._state_mark)

        self._message = QLabel("", frame)
        message_font = self._message.font()
        message_font.setBold(True)
        self._message.setFont(message_font)
        self._message.setWordWrap(True)
        self._message.setAccessibleName("Dictation status message")
        layout.addWidget(self._message, 1)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)
        self.state_requested.connect(self._render)
        self.exit_requested.connect(self._exit)

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

    @Slot(str, object)
    def _render(self, state: str, detail: object) -> None:
        symbol, default_text = self.STATES.get(state, self.STATES["error"])
        text = detail if isinstance(detail, str) and detail else default_text
        self._state_mark.setText(symbol)
        self._state_mark.setAccessibleDescription(text)
        self._message.setText(text)
        self.status_changed.emit(state, text)

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
