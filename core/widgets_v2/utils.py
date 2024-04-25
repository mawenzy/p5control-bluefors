from typing import Optional

from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QGridLayout, QWidget, QToolButton, QStyle, QLineEdit, QVBoxLayout

from p5control import InstrumentGateway, DataGateway

class StatusIndicator(QToolButton):
    """
    ``QToolButton``, which indicates a status, with either red or green background color.
    """
    def __init__(self):
        super().__init__()
        self.setDisabled(True)

        # start in off state
        self.state = False
        self._update_color()

    def _update_color(self):
        if self.state:
            self.setStyleSheet("background-color: green")
        else:
            self.setStyleSheet("background-color: red")

    def set_state(self, state: bool):
        """
        Set the state.

        Parameters
        ----------
        state : bool
            True -> green, False -> red
        """
        if self.state == state:
            return
        self.state = state
        self._update_color()

    def set_disabled(self):
        self.setStyleSheet("background-color: grey")

class PlayPauseButton(QToolButton):
    """
    QToolButton which switches beteen play and pause icon.
    """

    changed = Signal(bool)
    """
    **Signal(bool)** - emits ``self.playing`` if it changes
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.playing = False
        self._update_icon()

        self.clicked.connect(self._handle_click)

    def _handle_click(self):
        self.playing = not self.playing
        self._update_icon()
        self.changed.emit(self.playing)

    def _update_icon(self):
        if self.playing:
            self.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def set_playing(self, playing: bool):
        """
        Change playing parameter and upate icon

        Parameters
        ----------
        playing : bool
            state to set the button in
        """
        if self.playing == playing:
            return
        self.playing = playing
        self._update_icon()
        self.changed.emit(self.playing)


        
class DisabledLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setReadOnly(True)



# Adapted from https://github.com/nlamprian/pyqt5-led-indicator-widget/tree/master

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

class LedIndicator(QAbstractButton):
    scaledSize = 1000.0

    def __init__(self, parent=None, warning=False):
        self.warning = warning

        QAbstractButton.__init__(self, parent)
        self.setMinimumSize(24, 24)
        self.setCheckable(True)
        self.setDisabled(True)

        # seeblau
        self.on_color_1 = QColor(166, 225, 244)
        self.on_color_2 = QColor(89, 199, 235)

        # helles seegrau
        self.off_color_1 = QColor(154, 160, 167)
        self.off_color_2 = QColor(184, 188, 193)

        # warning rot
        self.warning_color_1 = QColor(176, 0, 0)
        self.warning_color_2 = QColor(255, 0, 0)

    def set_state(self, state):
        self.setChecked(state)

    def set_disabled(self):
        self.warning = False
        self.setChecked(False)

    def resizeEvent(self, QResizeEvent):
        self.update()

    def paintEvent(self, QPaintEvent):
        realSize = min(self.width(), self.height())

        painter = QPainter(self)
        pen = QPen(Qt.black)
        pen.setWidth(1)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(realSize / self.scaledSize, realSize / self.scaledSize)

        gradient = QRadialGradient(QPointF(-500, -500), 1500, QPointF(-500, -500))
        gradient.setColorAt(0, QColor(224, 224, 224))
        gradient.setColorAt(1, QColor(28, 28, 28))
        painter.setPen(pen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(0, 0), 500, 500)

        gradient = QRadialGradient(QPointF(500, 500), 1500, QPointF(500, 500))
        gradient.setColorAt(0, QColor(224, 224, 224))
        gradient.setColorAt(1, QColor(28, 28, 28))
        painter.setPen(pen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(0, 0), 450, 450)

        painter.setPen(pen)
        if self.isChecked():
            gradient = QRadialGradient(QPointF(-500, -500), 1500, QPointF(-500, -500))
            gradient.setColorAt(0, self.on_color_1)
            gradient.setColorAt(1, self.on_color_2)
        else:
            gradient = QRadialGradient(QPointF(500, 500), 1500, QPointF(500, 500))
            if self.warning:
                gradient.setColorAt(0, self.warning_color_1)
                gradient.setColorAt(1, self.warning_color_2)
            else:
                gradient = QRadialGradient(QPointF(500, 500), 1500, QPointF(500, 500))
                gradient.setColorAt(0, self.off_color_1)
                gradient.setColorAt(1, self.off_color_2)


        painter.setBrush(gradient)
        painter.drawEllipse(QPointF(0, 0), 400, 400)
