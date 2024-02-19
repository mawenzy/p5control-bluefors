from typing import Optional

from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QToolButton

from pyqtgraph import SpinBox

from p5control import InstrumentGateway, DataGateway
from ..utils import PlayPauseButton, StatusIndicator


from logging import getLogger
logger = getLogger(__name__)

from qtpy.QtWidgets import QComboBox

class DisabledLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setReadOnly(True)

class Adwinv4OutputControl(QWidget):
    """
    Widget to control AdwinOutputControl
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'AdwinOutputControl'

        self.gw = gw
        self.measure = self.gw.measure()

        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        self.id = self.dgw.register_callback("/status/adwin", lambda arr: self._handle_status_callback(arr))

        self.status_label = QLabel()
        self.status_label.setText("Output:")
        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()
        self.btn.changed.connect(self._handle_btn_change)
        self.btn.changed.connect(self.status_indicator.set_state)

        self.V1_off_label = QLabel()
        self.V1_off_label.setText("V1_off: (mV)")
        self.V1_off = QLabel()

        self.V2_off_label = QLabel()
        self.V2_off_label.setText("V2_off: (mV)")
        self.V2_off = QLabel()

        layout = QGridLayout()
        layout.addWidget(self.status_label, 0, 0)
        layout.addWidget(self.btn, 0, 1)
        layout.addWidget(self.status_indicator, 0, 2)

        layout.addWidget(self.V1_off_label, 1, 0)
        layout.addWidget(self.V1_off, 1, 1, 1, 2)

        layout.addWidget(self.V2_off_label, 2, 0)
        layout.addWidget(self.V2_off, 2, 1, 1, 2)

        layout.setColumnStretch(3,3)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)

    @Slot(bool)
    def _handle_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        self.gw.adwin.setOutput(playing)

    def _handle_status_callback(self, arr):
        logger.debug('%s._handle_status_callback()', self._name)
        output = bool(arr['output'][0])
        self.V1_off.setText(f"{float(arr['V1_off'][0]*1000):3.2f}")
        self.V2_off.setText(f"{float(arr['V2_off'][0]*1000):3.2f}")
        self.status_indicator.set_state(output)
        self.btn.set_playing(output)