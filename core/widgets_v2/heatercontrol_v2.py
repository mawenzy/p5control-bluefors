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
    Widget to control AMI430
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
            a = self.gw.heater
        except AttributeError:
            self.exist = False

        # TODO
        self.id = self.dgw.register_callback("/status/bluefors/something", lambda arr: self._handle_status_callback(arr))

        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()
        self.btn.changed.connect(self._handle_btn_change)

        self.sample_temperature = QLabel()
        self.mxc_temperature = QLabel()

        default_value = 0
        if self.exist:
            default_value = self.gw.magnet.get_target_field() #TODO
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

        layout.addWidget(QLabel("T_mxc: (mK)"), 3, 0)
        layout.addWidget(self.mxc_temperature, 3, 1, 1, 2)

        layout.setColumnStretch(3,3)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)

    def _handle_target_temperature(self):
        logger.debug('%s._handle_target_temperature()', self._name)
        # TODO

        # self.gw.magnet.set_target_field(float(self.target_field.value())/1000)

    def _handle_status_callback(self, arr):
        logger.debug('%s._handle_status_callback()', self._name)
        # TODO

        # field = arr['field'][0]
        # state = arr['state'][0]
        
        # self.actual_field.setText(f"{field*1000:.1f}")
        
        # if state == 1:
        #     self.status_indicator.set_state(True)
        #     self.btn.set_playing(True)
        # else:
        #     self.status_indicator.set_state(False)
        #     self.btn.set_playing(False)


    @Slot(bool)
    def _handle_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        # TODO
        # if playing:
        #     self.gw.magnet.ramp()
        # else:
        #     self.gw.magnet.pause()