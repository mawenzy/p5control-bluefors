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

class Adwinv4SweepControl(QWidget):
    """
    Widget to control AdwinSweepControl
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'AdwinSweepControl'

        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        self.id = self.dgw.register_callback("/status/adwin", lambda arr: self._handle_status_callback(arr))

        self.status_label = QLabel()
        self.status_label.setText("Sweeping:")
        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()
        self.btn.changed.connect(self._handle_btn_change)
        self.btn.changed.connect(self.status_indicator.set_state)

        self.amplitude_label = QLabel()
        self.amplitude_label.setText("Amplitude: (V)")
        self.amplitude = SpinBox(value=self.gw.adwin.getAmplitude(), bounds=[0, 10])
        self.amplitude.valueChanged.connect(self._handle_amplitude)

        self.period_label = QLabel()
        self.period_label.setText("Period /\\: (s)")
        self.period = SpinBox(value=self.gw.adwin.getPeriod(), bounds=[0, 1000])
        self.period.valueChanged.connect(self._handle_frequency)

        layout = QGridLayout()
        layout.addWidget(self.status_label, 0, 0)
        layout.addWidget(self.btn, 0, 1)
        layout.addWidget(self.status_indicator, 0, 2)

        layout.addWidget(self.amplitude_label, 1, 0)
        layout.addWidget(self.amplitude, 1, 1, 1, 2)

        layout.addWidget(self.period_label, 2, 0)
        layout.addWidget(self.period, 2, 1, 1, 2)
        
        layout.setColumnStretch(3,3)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)

    def _handle_amplitude(self):
        logger.debug('%s._handle_amplitude()', self._name)
        self.gw.adwin.setAmplitude(float(self.amplitude.value()))

    def _handle_frequency(self):
        logger.debug('%s._handle_amplitude()', self._name)
        self.gw.adwin.setPeriod(float(self.period.value()))

    @Slot(bool)
    def _handle_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        self.gw.adwin.setSweeping(playing)

    def _handle_status_callback(self, arr):
        logger.debug('%s._handle_status_callback()', self._name)
        sweeping = bool(arr['sweeping'][0])
        self.status_indicator.set_state(sweeping)
        self.btn.set_playing(sweeping)