from __future__ import annotations

import sys

from PySide6.QtCore import QLineF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication

BRAGI_ORANGE = QColor("#F05A24")

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


def bragi_icon(size: int = 64) -> QIcon:
    """Create Bragi's dot-and-speaking-marks icon in memory."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    dot_radius = size * 0.115
    dot_x = size * 0.27
    dot_y = size * 0.50
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(BRAGI_ORANGE)
    painter.drawEllipse(
        QRectF(
            dot_x - dot_radius,
            dot_y - dot_radius,
            dot_radius * 2,
            dot_radius * 2,
        )
    )

    mark_pen = QPen(BRAGI_ORANGE)
    mark_pen.setWidthF(max(2.0, size * 0.105))
    mark_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(mark_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawLine(QLineF(size * 0.54, size * 0.39, size * 0.72, size * 0.29))
    painter.drawLine(QLineF(size * 0.56, size * 0.50, size * 0.80, size * 0.50))
    painter.drawLine(QLineF(size * 0.54, size * 0.61, size * 0.72, size * 0.71))
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
    app.setStyleSheet(APP_STYLESHEET)
    return app
