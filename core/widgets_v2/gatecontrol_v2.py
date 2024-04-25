from p5control import InstrumentGateway, DataGateway

from typing import Optional
from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QToolButton
from pyqtgraph import SpinBox
from .utils import PlayPauseButton, StatusIndicator, LedIndicator
import numpy as np
from qtpy.QtWidgets import QComboBox
from logging import getLogger
logger = getLogger(__name__)

class GateControl(QWidget):
    """
    Widget to control Adwin Sensory Unit
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'GateControl'
        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        self.exist = True
        try:
            a = self.gw.gate
        except AttributeError:
            self.exist = False

        self.id = self.dgw.register_callback("/status/gate", lambda arr: self._handle_status_callback(arr))

        self.status_indicator = LedIndicator(warning=False)
        if not self.exist:
            self.status_indicator.setChecked(False)
        self.btn = PlayPauseButton()
        self.btn.changed.connect(self._handle_btn_change)
        if self.exist:
            self.btn.set_playing(self.gw.gate.getOutput())
            
        default_value = 0
        if self.exist:
            default_value = self.gw.gate.getVoltage()
        self.voltage = SpinBox(value=default_value, bounds=[-10, 10])
        self.voltage.valueChanged.connect(self._handle_voltage)

        lay = QGridLayout()

        lay.addWidget(QLabel("Output:"), 0, 0)
        lay.addWidget(self.btn, 0, 1)
        lay.addWidget(self.status_indicator, 0, 2)
        lay.addWidget(QLabel("Voltage: (V)"), 1, 0)
        lay.addWidget(self.voltage, 1, 1, 1, 2)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(lay)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)

    @Slot(bool)
    def _handle_voltage(self):
        logger.debug('%s._handle_voltage()', self._name)
        self.gw.gate.setVoltage(float(self.voltage.value()))

    def _handle_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        self.gw.gate.setOutput(playing)

    def _handle_status_callback(self, arr):
        logger.debug('%s._handle_status_callback()', self._name)
        pass
        # TODO
        # leak current?

'''
Requires gate:
- getVoltage()
- setVoltage()
- getOutput()
- setOutput()

TODO:
status? leakcurrent?
'''