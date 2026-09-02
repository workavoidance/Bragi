from __future__ import annotations

import sys

from PySide6.QtCore import QLineF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication

SKRIVI_INK = QColor("#181817")
SKRIVI_ICON_EDGE = QColor("#FFFDF9")
SKRIVI_ICON_SIZES = (16, 20, 24, 32, 48, 64, 128, 256)

APP_STYLESHEET = """
QDialog {
    background: #FAF7F2;
    color: #181817;
}
QLabel, QCheckBox, QGroupBox, QTabWidget {
    color: #181817;
}
QGroupBox {
    background: #FFFDF9;
    border: 1px solid #DED7CF;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
QTabWidget::pane {
    background: #FFFDF9;
    border: 1px solid #DED7CF;
    border-radius: 10px;
    top: -1px;
}
QTabBar::tab {
    color: #6F6A63;
    padding: 9px 14px;
}
QTabBar::tab:selected {
    color: #181817;
    border-bottom: 3px solid #F05A24;
}
QPushButton {
    background: #FFFDF9;
    color: #181817;
    border: 1px solid #DED7CF;
    border-radius: 8px;
    padding: 7px 14px;
}
QPushButton:hover {
    border-color: #F05A24;
}
QPushButton:default {
    background: #F05A24;
    border-color: #F05A24;
    color: #181817;
    font-weight: 600;
}
QMenu {
    background: #FFFDF9;
    color: #181817;
    border: 1px solid #DED7CF;
}
QMenu::item:selected {
    background: #FFE2D5;
}
"""


def _skrivi_icon_pixmap(size: int) -> QPixmap:
    """Render a high-contrast Skrivi mark at one native icon size."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    dot_radius = size * 0.14
    dot_x = size * 0.17
    dot_y = size * 0.50
    painter.setPen(Qt.PenStyle.NoPen)
    edge_width = max(1.0, size * 0.045)
    painter.setBrush(SKRIVI_ICON_EDGE)
    painter.drawEllipse(
        QRectF(
            dot_x - dot_radius - edge_width,
            dot_y - dot_radius - edge_width,
            (dot_radius + edge_width) * 2,
            (dot_radius + edge_width) * 2,
        )
    )
    painter.setBrush(SKRIVI_INK)
    painter.drawEllipse(
        QRectF(
            dot_x - dot_radius,
            dot_y - dot_radius,
            dot_radius * 2,
            dot_radius * 2,
        )
    )

    lines = (
        QLineF(size * 0.50, size * 0.38, size * 0.78, size * 0.17),
        QLineF(size * 0.52, size * 0.50, size * 0.94, size * 0.50),
        QLineF(size * 0.50, size * 0.62, size * 0.78, size * 0.83),
    )
    mark_width = max(2.0, size * 0.13)
    edge_pen = QPen(SKRIVI_ICON_EDGE)
    edge_pen.setWidthF(mark_width + edge_width * 2)
    edge_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(edge_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for line in lines:
        painter.drawLine(line)

    mark_pen = QPen(SKRIVI_INK)
    mark_pen.setWidthF(mark_width)
    mark_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(mark_pen)
    for line in lines:
        painter.drawLine(line)
    painter.end()
    return pixmap


def skrivi_icon() -> QIcon:
    """Create Skrivi's readable multi-size tray and application icon."""
    icon = QIcon()
    for size in SKRIVI_ICON_SIZES:
        icon.addPixmap(_skrivi_icon_pixmap(size))
    return icon


def create_application(title: str) -> QApplication:
    """Return Skrivi's single Qt application instance."""
    existing = QApplication.instance()
    if existing is not None:
        app = existing
    else:
        app = QApplication(sys.argv)
    app.setApplicationName("Skrivi")
    app.setApplicationDisplayName(title)
    app.setOrganizationName("Skrivi")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(skrivi_icon())
    app.setStyleSheet(APP_STYLESHEET)
    return app
