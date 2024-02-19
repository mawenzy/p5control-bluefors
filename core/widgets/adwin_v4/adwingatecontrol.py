from typing import Optional

from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QToolButton

from pyqtgraph import SpinBox

from p5control import InstrumentGateway, DataGateway
from ..utils import PlayPauseButton, StatusIndicator


from qtpy.QtWidgets import QComboBox

from logging import getLogger
logger = getLogger(__name__)

class DisabledLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setReadOnly(True)

class Adwinv4GateControl(QWidget):
    """
    Widget to control AdwinGateControl
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'AdwinGateControl'

        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        self.id = self.dgw.register_callback("/status/adwin", lambda arr: self._handle_status_callback(arr))

        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()
        self.btn.changed.connect(self._handle_btn_change)
        self.btn.changed.connect(self.status_indicator.set_state)

        self.amplitude_label = QLabel()
        self.amplitude_label.setText("Amplitude: (V)")
        self.amplitude = SpinBox(value=self.gw.adwin.getGateAmplitude(), bounds=[0, 10])
        self.amplitude.valueChanged.connect(self._handle_amplitude)

        layout = QGridLayout()
        layout.addWidget(self.status_indicator, 0, 0)
        layout.addWidget(self.btn, 0, 1)

        layout.addWidget(self.amplitude_label, 1, 0, 1, 2)
        layout.addWidget(self.amplitude, 1, 2)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)

    def _handle_amplitude(self):
        logger.debug('%s._handle_amplitude()', self._name)
        self.gw.adwin.setGateAmplitude(float(self.amplitude.value()))

    @Slot(bool)
    def _handle_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        self.gw.adwin.setGating(playing)

    def _handle_status_callback(self, arr):
        logger.debug('%s._handle_status_callback()', self._name)
        sweeping = bool(arr['gate'][0])
        self.status_indicator.set_state(sweeping)
        self.btn.set_playing(sweeping)