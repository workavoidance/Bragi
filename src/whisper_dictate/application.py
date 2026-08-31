from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication

BRAGI_ORANGE = QColor("#E86A33")


def bragi_icon(size: int = 64) -> QIcon:
    """Create the tray icon in memory so source and packaged runs match."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(BRAGI_ORANGE)
    painter.drawEllipse(2, 2, size - 4, size - 4)

    white = QPen(Qt.GlobalColor.white)
    white.setWidth(max(3, size // 16))
    white.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(white)
    painter.setBrush(Qt.GlobalColor.white)
    painter.drawRoundedRect(
        size * 3 // 8,
        size // 5,
        size // 4,
        size * 2 // 5,
        size // 8,
        size // 8,
    )
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(
        size * 9 // 32,
        size * 5 // 16,
        size * 7 // 16,
        size * 7 // 16,
        0,
        -180 * 16,
    )
    painter.drawLine(size // 2, size * 3 // 4, size // 2, size * 13 // 16)
    painter.drawLine(size * 3 // 8, size * 13 // 16, size * 5 // 8, size * 13 // 16)
    painter.end()
    return QIcon(pixmap)


def create_application(title: str) -> QApplication:
    """Return Bragi's single Qt application instance."""
    existing = QApplication.instance()
    if existing is not None:
        app = existing
    else:
        app = QApplication(sys.argv)
    app.setApplicationName("Bragi")
    app.setApplicationDisplayName(title)
    app.setOrganizationName("Bragi")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(bragi_icon())
    return app
