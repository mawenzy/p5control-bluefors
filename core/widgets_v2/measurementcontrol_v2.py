from p5control import InstrumentGateway, DataGateway

from typing import Optional
from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QToolButton
from pyqtgraph import SpinBox
from .utils import PlayPauseButton, StatusIndicator
import numpy as np
from qtpy.QtWidgets import QComboBox
from logging import getLogger
logger = getLogger(__name__)

class MeasurementControl(QWidget):
    """
    Widget to control measurements. Lets you run and pause them and change the name.
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        show_selector=True,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self.gw = gw

        # widgets
        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()
        self.name = QLineEdit()

        self.btn.changed.connect(self._handle_btn_change)
        self.btn.changed.connect(self.status_indicator.set_state)

        # layout
        layout = QGridLayout()
        layout.addWidget(QLabel('Measure:'), 0, 0)
        layout.addWidget(self.btn, 0, 1)
        layout.addWidget(QLabel('Name:'), 0, 2)
        layout.addWidget(self.name, 0, 3)
        layout.addWidget(self.status_indicator, 0, 4)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        layout.setColumnStretch(3,3)

        # get first measurement
        self.gw_update()

    @Slot(bool)
    def _handle_btn_change(self, playing: bool):
        # disable button while we handle operation
        self.btn.setEnabled(False)

        # disable line edit when measurement is running
        if playing:
            self.name.setEnabled(False)
        else:
            self.name.setEnabled(True)

        measure = self.gw.measure(self.name.text())
        if playing and not measure.running:
            measure.start()
        elif not playing and measure.running:
            measure.stop()

        self.btn.setEnabled(True)

    def gw_update(self):
        """
        Update the widget by requesting the Measurement object from the instrument server and
        reading its state into this widget.
        """
        measure = self.gw.measure()
        self.last_name = measure.name

        self.name.setText(measure.name)
        self.btn.set_playing(measure.running)
