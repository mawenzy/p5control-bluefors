from typing import Optional

from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QGridLayout

from pyqtgraph import SpinBox

from p5control import InstrumentGateway, DataGateway
from .utils import PlayPauseButton, StatusIndicator
from core.utilities.config import dump_to_config, load_from_config

from qtpy.QtWidgets import QComboBox


from logging import getLogger
logger = getLogger(__name__)


class MotorControl(QWidget):
    """
    Widget to control Faulhaber motor / breakjunction mechanics
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'MotorControl'

        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        self.status_label = QLabel()
        self.status_label.setText("Moving:")
        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()
        self.btn.changed.connect(self._handle_btn_change)

        self.position_label = QLabel()
        self.position_label.setText("Position: ")
        self.position = QLabel()
        
        motor_dict = load_from_config('motor')
        lower = motor_dict['lower_limit']*1e-8
        upper = motor_dict['upper_limit']*1e-8

        self.target_pos_label = QLabel()
        self.target_pos_label.setText("Target:")
        self.target_pos = SpinBox(value=self.gw.motor.get_target_position(), bounds=[lower, upper])
        self.target_pos.valueChanged.connect(self._handle_target_pos)

        self.target_speed_label = QLabel()
        self.target_speed_label.setText("Speed:")
        self.target_speed = SpinBox(value=self.gw.motor.get_target_speed(), bounds=[20, 7000], int=True)
        self.target_speed.valueChanged.connect(self._handle_target_speed)

        self.id = self.dgw.register_callback("/status/motor", lambda arr: self._handle_status_callback(arr))

        layout = QGridLayout()
        layout.addWidget(self.status_label, 0, 0)
        layout.addWidget(self.btn, 0, 1)
        layout.addWidget(self.status_indicator, 0, 2)

        layout.addWidget(self.position_label, 1, 0)
        layout.addWidget(self.position, 1, 1, 1, 2)

        layout.addWidget(self.target_pos_label, 2, 0)
        layout.addWidget(self.target_pos, 2, 1, 1, 2)

        layout.addWidget(self.target_speed_label, 3, 0)
        layout.addWidget(self.target_speed, 3, 1, 1, 2)

        layout.setColumnStretch(3,3)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()


        logger.debug('%s initialized.', self._name)

    def _handle_target_pos(self):
        logger.debug('%s._handle_target_pos()', self._name)
        self.gw.motor.set_target_position(float(self.target_pos.value()))

    def _handle_target_speed(self):
        logger.debug('%s._handle_target_speed()', self._name)
        self.gw.motor.set_target_speed(float(self.target_speed.value()))

    def _handle_status_callback(self, arr):
        logger.debug('%s._handle_status_callback()', self._name)
        pos = arr['position'][0]
        self._moving = arr['moving'][0]
        # print(self.T, self._moving)
        self.status_indicator.set_state(self._moving)
        self.btn.set_playing(self._moving)
        self.position.setText(f"{pos:.3f}")

    @Slot(bool)
    def _handle_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        self.gw.motor.set_moving(playing)