from typing import Optional

from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QToolButton

from pyqtgraph import SpinBox

from p5control import InstrumentGateway, DataGateway
from p5control.gui.widgets.measurementcontrol import PlayPauseButton, StatusIndicator

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

class AdwinSensorControl(QWidget):
    """
    Widget to control Adwin Sensory Unit
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'AdwinSensorControl'

        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        # self.id = self.dgw.register_callback("/status/adwin", lambda arr: self._handle_status_callback(arr))

        self.range_1 = QComboBox()
        self.range_1.addItems(['10.00', ' 5.00', ' 2.50', ' 1.25'])
        self.range_1.activated.connect(self.onChanged_ch1)

        self.range_2 = QComboBox()
        self.range_2.addItems(['10.00', ' 5.00', ' 2.50', ' 1.25'])
        self.range_2.activated.connect(self.onChanged_ch2)

        self.averaging = SpinBox(value=self.gw.adwin.averaging, bounds=[1, 100000], int=True)
        self.averaging.valueChanged.connect(self._handle_averaging)

        self.range_1_label = QLabel()
        self.range_1_label.setText('Range V1 (V)')

        self.range_2_label = QLabel()
        self.range_2_label.setText('Range V2 (V)')
        
        self.averaging_label = QLabel()
        self.averaging_label.setText("Averaging: ")


        layout = QGridLayout()

        layout.addWidget(self.range_1_label, 0, 0)
        layout.addWidget(self.range_1, 0, 1)

        layout.addWidget(self.range_2_label, 1, 0)
        layout.addWidget(self.range_2, 1, 1)

        layout.addWidget(self.averaging_label, 2, 0)
        layout.addWidget(self.averaging, 2, 1)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)

    # def _handle_status_callback(self, arr):
    #     range_ch1 = arr['range_ch1'][0]
    #     range_ch2 = arr['range_ch2'][0]
    #     averaging = arr['averaging'][0]

    #     self.averaging.setValue(averaging)

    #     # ranges = np.array([10, 5, 2.5, 1.25])
    #     # index_ch1 = int(np.argmin(np.abs(ranges-int(range_ch1))))
    #     # index_ch2 = int(np.argmin(np.abs(ranges-int(range_ch2))))
    #     # self.range_1.setCurrentIndex(index_ch1)
    #     # self.range_2.setCurrentIndex(index_ch2)
        
    def _handle_averaging(self):
        logger.debug('%s._handle_averaging()', self._name)
        self.gw.adwin.setAveraging(int(self.averaging.value()))

    def onChanged_ch1(self, index):
        logger.debug('%s.onChanged_ch1(%s)', self._name, index)
        ranges=[10, 5, 2.5, 1.25]
        self.gw.adwin.setRange(range=ranges[index], ch=1)

    def onChanged_ch2(self, index):
        logger.debug('%s.onChanged_ch2(%s)', self._name, index)
        ranges=[10, 5, 2.5, 1.25]
        self.gw.adwin.setRange(range=ranges[index], ch=2)