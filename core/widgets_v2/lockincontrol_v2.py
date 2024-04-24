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

class LockinControl(QWidget):
    """
    Widget to control Adwin Sensory Unit
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'LockinControl'
        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        self.exist = True
        try:
            a = self.gw.lockin
        except AttributeError:
            self.exist = False

        self.id = self.dgw.register_callback("/status/lockin", lambda arr: self._handle_status_callback(arr))

        self.status_indicator = StatusIndicator()
        if not self.exist:
            self.status_indicator.set_disabled()
        self.btn = PlayPauseButton()
        self.btn.changed.connect(self._handle_btn_change)
            
        default_value = 0
        if self.exist:
            default_value = 10 # TODO
            pass
        self.frequency = SpinBox(value=default_value, bounds=[0, 1e5])
        self.frequency.valueChanged.connect(self._handle_frequency)

        default_value = 0
        if self.exist:
            default_value = 0 # TODO
            pass
        self.amplitude = SpinBox(value=default_value, bounds=[0, 1])
        self.amplitude.valueChanged.connect(self._handle_amplitude)

        default_value = 0
        if self.exist:
            default_value = 0 # TODO
            pass
        self.sample_rate = SpinBox(value=default_value, bounds=[0, 1])
        self.sample_rate.valueChanged.connect(self._handle_sample_rate)

        lay = QGridLayout()

        lay.addWidget(QLabel("Output:"), 0, 0)
        lay.addWidget(self.btn, 0, 1)
        lay.addWidget(self.status_indicator, 0, 2)
        lay.addWidget(QLabel("Frequency: (Hz)"), 1, 0)
        lay.addWidget(self.frequency, 1, 1, 1, 2)
        lay.addWidget(QLabel("Amplitude: (V)"), 2, 0)
        lay.addWidget(self.amplitude, 2, 1, 1, 2)
        lay.addWidget(QLabel("Sample Rate: (Hz)"), 3, 0)
        lay.addWidget(self.sample_rate, 3, 1, 1, 2)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(lay)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)

    @Slot(bool)
    def _handle_frequency(self):
        logger.debug('%s._handle_frequency()', self._name)
        #self.gw.vna.setTSweepFrequency(float(self.frequency.value())*1e9)

    def _handle_amplitude(self):
        logger.debug('%s._handle_amplitude()', self._name)
        #self.gw.vna.setPower(float(self.power.value()))

    def _handle_sample_rate(self):
        logger.debug('%s._handle_sample_rate()', self._name)
        #self.gw.vna.setPower(float(self.power.value()))

    def _handle_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        # self.gw.vna.setOutput(playing)
        # self.status_indicator.set_state(playing)
        # self.btn.set_playing(playing)

    def _handle_status_callback(self, arr):
        logger.debug('%s._handle_status_callback()', self._name)
        pass
        # TODO
        # leak current?

'''
Lockin complett
'''