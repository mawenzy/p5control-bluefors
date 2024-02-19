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