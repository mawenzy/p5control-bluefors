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

        self.id = self.dgw.register_callback("/status/magnet", lambda arr: self._handle_status_callback(arr))

        self.status_label = QLabel()
        self.status_label.setText("Ramping:")
        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()
        self.btn.changed.connect(self._handle_btn_change)
        # self.state_indicator = QLabel()

        self.actual_field_label = QLabel()
        self.actual_field_label.setText("Field: (mT)")
        self.actual_field = QLabel()

        self.target_field_label = QLabel()
        self.target_field_label.setText("Target: (mT)")
        self.target_field = SpinBox(value=self.gw.magnet.get_target_field()*1000, bounds=[-7000, 7000])
        self.target_field.valueChanged.connect(self._handle_target_field)

        self.rate_label = QLabel()
        self.rate_label.setText("Rate: (mT/min)")
        self.rate = SpinBox(value=self.gw.magnet.get_rate()*1000, bounds=[0, 210.6])
        self.rate.valueChanged.connect(self._handle_rate)

        layout = QGridLayout()
        layout.addWidget(self.status_label, 0, 0)
        layout.addWidget(self.btn, 0, 1)
        layout.addWidget(self.status_indicator, 0, 2)
        # layout.addWidget(self.state_indicator, 0, 2)

        layout.addWidget(self.actual_field_label, 1, 0)
        layout.addWidget(self.actual_field, 1, 1, 1, 2)

        layout.addWidget(self.target_field_label, 2, 0)
        layout.addWidget(self.target_field, 2, 1, 1, 2)

        layout.addWidget(self.rate_label, 3, 0)
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
        # rate = arr['rate'][0]
        # target = arr['target'][0]
        
        self.actual_field.setText(f"{field*1000:.1f}")
        # self.state_indicator.setText("%i"%state)
        # self.target_field.setValue(target*1000)
        # self.rate.setValue(rate*1000)
        
        if state == 1:
            self.status_indicator.set_state(True)
            self.btn.set_playing(True)
        else:
            self.status_indicator.set_state(False)
            self.btn.set_playing(False)


    @Slot(bool)
    def _handle_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        if playing:
            self.gw.magnet.ramp()
        else:
            self.gw.magnet.pause()