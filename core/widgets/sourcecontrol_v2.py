from typing import Optional

from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QToolButton, QBoxLayout

from pyqtgraph import SpinBox

from p5control import InstrumentGateway, DataGateway
from .utils import PlayPauseButton, StatusIndicator


from logging import getLogger
logger = getLogger(__name__)


from qtpy.QtWidgets import QComboBox

class DisabledLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setReadOnly(True)

class SourceControl_v2(QWidget):
    """
    Widget to control AMI430
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'SourceControl_v2'

        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        self.id = self.dgw.register_callback("/status/source", lambda arr: self._handle_status_callback(arr))

        self.output_status_label = QLabel()
        self.output_status_label.setText("Output:")
        self.output_status_indicator = StatusIndicator()
        self.output_btn = PlayPauseButton()
        self.output_btn.changed.connect(self._handle_output_btn_change)

        self.sweeping_status_label = QLabel()
        self.sweeping_status_label.setText("Sweeping:")
        self.sweeping_status_indicator = StatusIndicator()
        self.sweeping_btn = PlayPauseButton()
        self.sweeping_btn.changed.connect(self._handle_sweeping_btn_change)

        self.amplitude_label = QLabel()
        self.amplitude_label.setText("Amplitude: (V)")
        self.amplitude = SpinBox(value=self.gw.source.get_amplitude(), bounds=[-10, 10])
        self.amplitude.valueChanged.connect(self._handle_amplitude)

        self.period_label = QLabel()
        self.period_label.setText("Period /\: (s)")
        self.period = SpinBox(value=self.gw.source.get_period(), bounds=[0, 7200])
        self.period.valueChanged.connect(self._handle_period)

        layout = QGridLayout()
        layout.addWidget(self.output_status_label, 0, 0)
        layout.addWidget(self.output_btn, 0, 1)
        layout.addWidget(self.output_status_indicator, 0, 2)
        
        layout.addWidget(self.sweeping_status_label, 1, 0)
        layout.addWidget(self.sweeping_btn, 1, 1)
        layout.addWidget(self.sweeping_status_indicator, 1, 2)

        layout.addWidget(self.amplitude_label, 2, 0)
        layout.addWidget(self.amplitude, 2, 1, 1, 2)

        layout.addWidget(self.period_label, 3, 0)
        layout.addWidget(self.period, 3, 1, 1, 2)

        layout.setColumnStretch(3,3)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)
        
    def _handle_status_callback(self, arr):
        logger.debug('%s._handle_status_callback()', self._name)
        output = arr['output'][0]
        self.output_status_indicator.set_state(output)
        self.output_btn.set_playing(output)

        sweeping = arr['sweeping'][0]
        self.sweeping_status_indicator.set_state(sweeping)
        self.sweeping_btn.set_playing(sweeping)

    def _handle_amplitude(self):
        logger.debug('%s._handle_amplitude()', self._name)
        self.gw.source.set_amplitude(float(self.amplitude.value()))

    def _handle_period(self):
        logger.debug('%s._handle_period()', self._name)
        self.gw.source.set_rate(float(self.period.value()))

    @Slot(bool)
    def _handle_output_btn_change(self, playing:bool):
        logger.debug('%s._handle_output_btn_change(%s)', self._name, playing)
        self.gw.source.set_output(playing)

    @Slot(bool)
    def _handle_sweeping_btn_change(self, playing:bool):
        logger.debug('%s._handle_sweeping_btn_change(%s)', self._name, playing)
        self.gw.source.set_sweeping(playing)