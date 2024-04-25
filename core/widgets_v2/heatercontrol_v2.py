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

class HeaterControl(QWidget):
    """
    Widget to control BlueFors API
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'HeaterControl'
        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        self.exist = True
        try:
            # TODO
            a = self.gw.bluefors
        except AttributeError:
            self.exist = False

        # TODO
        self.heater_id   = self.dgw.register_callback("/status/bluefors/heater/sampleheater", lambda arr: self._handle_status_callback_heater(arr))
        self.T_sample_id = self.dgw.register_callback("/status/bluefors/temperature/sample",  lambda arr: self._handle_status_callback_Tsample(arr))
        # self.T_mxc_id = self.dgw.register_callback("/status/bluefors/temperature/mxc", lambda arr: self._handle_status_callback_Tmxc(arr))

        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()
        if not self.exist:
            self.status_indicator.set_disabled()
        else:
            self.btn.set_playing(self.gw.bluefors.getSampleHeater())
        self.btn.changed.connect(self._handle_btn_change)

        self.sample_temperature = QLabel()
        # self.mxc_temperature = QLabel()

        default_value = 0
        if self.exist:
            default_value = self.gw.bluefors.getTargetSampleTemperature()
        self.target_temperature = SpinBox(value=default_value, bounds=[0, 1500])
        self.target_temperature.valueChanged.connect(self._handle_target_temperature)

        layout = QGridLayout()
        layout.addWidget(QLabel("Heating:"), 0, 0)
        layout.addWidget(self.btn, 0, 1)
        layout.addWidget(self.status_indicator, 0, 2)

        layout.addWidget(QLabel("T_sample: (mK)"), 1, 0)
        layout.addWidget(self.sample_temperature, 1, 1, 1, 2)

        layout.addWidget(QLabel("Target: (mK)"), 2, 0)
        layout.addWidget(self.target_temperature, 2, 1, 1, 2)

        layout.setColumnStretch(3,3)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)

    def _handle_status_callback_heater(self, arr):
        logger.debug('%s._handle_status_callback_heater()', self._name)
        self.status_indicator.set_state(arr[0][1])

    def _handle_status_callback_Tsample(self, arr):
        logger.debug('%s._handle_status_callback_Tsample()', self._name)
        temperature = arr[0][1]
        self.sample_temperature.setText(f"{temperature*1000:.1f}")

    def _handle_target_temperature(self, value):
        logger.debug('%s._handle_target_temperature()', self._name)
        self.gw.bluefors.setTargetSampleTemperature(float(value))

    @Slot(bool)
    def _handle_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        self.gw.bluefors.setSampleHeater(playing)