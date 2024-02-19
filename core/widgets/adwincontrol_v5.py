from typing import Optional

from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QToolButton

from pyqtgraph import SpinBox

from p5control import InstrumentGateway, DataGateway
from .utils import PlayPauseButton, StatusIndicator

import numpy as np
from qtpy.QtWidgets import QComboBox


from logging import getLogger
logger = getLogger(__name__)


# class StatusIndicator(QToolButton):
#     """
#     ``QToolButton``, which indicates a status, with either red or green background color.
#     """
#     def __init__(self):
#         super().__init__()
#         self.setDisabled(True)

#         # start in off state
#         self.state = False
#         self._update_color()

#     def _update_color(self):
#         if self.state:
#             self.setStyleSheet("image: url(Zeichnung.png)")
#         else:
#             self.setIcon(QIcon())

    # def set_state(self, state: bool):
    #     """
    #     Set the state.

    #     Parameters
    #     ----------
    #     state : bool
    #         True -> green, False -> red
    #     """
    #     if self.state == state:
    #         return
    #     self.state = state
    #     self._update_color()

class DisabledLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setReadOnly(True)

class AdwinControl_v5(QWidget):
    """
    Widget to control Adwin Sensory Unit
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'AdwinControl_v5'

        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        self.id = self.dgw.register_callback("/status/adwin", lambda arr: self._handle_status_callback(arr))

        self.averaging_label = QLabel()
        self.averaging_label.setText("Averaging: ")
        self.averaging = SpinBox(value=self.gw.adwin.averaging, bounds=[1, 100000], int=True)
        self.averaging.valueChanged.connect(self._handle_averaging)
        
        self.offset_status_label = QLabel()
        self.offset_status_label.setText("Offsets:")
        self.offset_status_indicator = StatusIndicator()
        self.offset_btn = PlayPauseButton()
        self.offset_btn.changed.connect(self._handle_offset_btn_change)
        self.offset_btn.changed.connect(self.offset_status_indicator.set_state)

        self.calc_status_label = QLabel()
        self.calc_status_label.setText("Calculations:")
        self.calc_status_indicator = StatusIndicator()
        self.calc_btn = PlayPauseButton()
        self.calc_btn.changed.connect(self._handle_calc_btn_change)
        self.calc_btn.changed.connect(self.calc_status_indicator.set_state)

        
        self.offset = QLabel()
        self.offset_label = QLabel()
        self.offset_label.setText('V_off: (V)')
       
        layout = QGridLayout()

        layout.addWidget(self.offset_status_label, 1, 0)
        layout.addWidget(self.offset_btn, 1, 1)
        layout.addWidget(self.offset_status_indicator, 1, 2)

        layout.addWidget(self.calc_status_label, 2, 0)
        layout.addWidget(self.calc_btn, 2, 1)
        layout.addWidget(self.calc_status_indicator, 2, 2)

        layout.addWidget(self.averaging_label, 3, 0)
        layout.addWidget(self.averaging, 3, 1, 1, 2)

        layout.addWidget(self.offset_label, 4, 0)
        layout.addWidget(self.offset, 4, 1, 1, 2)

        layout.setColumnStretch(3,3)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)

    def _handle_status_callback(self, arr):
        logger.debug('%s._handle_status_callback()', self._name)
        self.offset.setText(f"{float(arr['V1_off'][0]*1000):3.2f}, {float(arr['V2_off'][0]*1000):3.2f}")
        
    def _handle_averaging(self):
        logger.debug('%s._handle_averaging()', self._name)
        self.gw.adwin.setAveraging(int(self.averaging.value()))

    @Slot(bool)
    def _handle_offset_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        self.gw.adwin.setOffseting(playing)
        
    @Slot(bool)
    def _handle_calc_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        self.gw.adwin.setCalculating(playing)