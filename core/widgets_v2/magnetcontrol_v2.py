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

class MagnetControl(QWidget):
    """
    Widget to control AMI430
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'MagnetControl'
        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        self.exist = True
        try:
            a = self.gw.magnet
        except AttributeError:
            self.exist = False

        self.id = self.dgw.register_callback("/status/magnet", lambda arr: self._handle_status_callback(arr))

        self.status_indicator = LedIndicator(warning=False)
        if not self.exist:
            self.status_indicator.setChecked(False)
        self.btn = PlayPauseButton()
        self.btn.changed.connect(self._handle_btn_change)

        self.actual_field = QLabel()

        default_value = 0
        if self.exist:
            default_value = self.gw.magnet.get_target_field()
        self.target_field = SpinBox(value=default_value*1000, bounds=[-7000, 7000])
        self.target_field.valueChanged.connect(self._handle_target_field)

        default_value = 0
        if self.exist:
            default_value = self.gw.magnet.get_rate()
        self.rate = SpinBox(value=default_value*1000, bounds=[0, 210.6])
        self.rate.valueChanged.connect(self._handle_rate)

        layout = QGridLayout()
        layout.addWidget(QLabel("Ramping:"), 0, 0)
        layout.addWidget(self.btn, 0, 1)
        layout.addWidget(self.status_indicator, 0, 2)

        layout.addWidget(QLabel("Field: (mT)"), 1, 0)
        layout.addWidget(self.actual_field, 1, 1, 1, 2)

        layout.addWidget(QLabel("Target: (mT)"), 2, 0)
        layout.addWidget(self.target_field, 2, 1, 1, 2)

        layout.addWidget(QLabel("Rate: (mT/min)"), 3, 0)
        layout.addWidget(self.rate, 3, 1, 1, 2)

        layout.setColumnStretch(3,3)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)

    def _handle_target_field(self):
        logger.debug('%s._handle_target_field()', self._name)
        self.gw.magnet.set_target_field(float(self.target_field.value())/1000)

    def _handle_rate(self):
        logger.debug('%s._handle_rate()', self._name)
        self.gw.magnet.set_rate(float(self.rate.value())/1000)

    def _handle_status_callback(self, arr):
        logger.debug('%s._handle_status_callback()', self._name)
        
        field = arr['field'][0]
        state = arr['state'][0]
        
        self.actual_field.setText(f"{field*1000:.1f}")
        
        if state == 1:
            self.status_indicator.setChecked(True)
            self.btn.set_playing(True)
        else:
            self.status_indicator.setChecked(False)
            self.btn.set_playing(False)


    @Slot(bool)
    def _handle_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        if playing:
            self.gw.magnet.ramp()
        else:
            self.gw.magnet.pause()