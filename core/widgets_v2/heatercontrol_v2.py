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

class HeaterControl(QWidget):
    """
    Widget to control BlueFors API
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
            a = self.gw.bluefors
        except AttributeError:
            self.exist = False

        if self.exist:
            self.heater_id   = self.dgw.register_callback(
                "/status/bluefors/driver", 
                lambda arr: self._handle_status_callback_driver(arr))
            self.T_sample_id = self.dgw.register_callback(
                "/status/bluefors/temperature/A-sample",  
                lambda arr: self._handle_status_callback_Tsample(arr))
            self.Heater_Power_id = self.dgw.register_callback(
                "/status/bluefors/heater/output_power",  
                lambda arr: self._handle_status_callback_HeaterPower(arr))
           
        ### PID
        self.pid_line = QLineEdit()
        self.pid_line.setText(f'{self.gw.bluefors.getP():.1f}, {self.gw.bluefors.getI():.1f}, {self.gw.bluefors.getD():.1f}')
        self.pid_line.textChanged[str].connect(self._handle_pid)

        ## Button + Status Indicators
        self.btn_pid = PlayPauseButton()
        self.btn_pid.changed.connect(self._handle_btn_change_pid)

        self.status_indicator_pid = LedIndicator(warning=False)
        if not self.exist:
            self.status_indicator_pid.setChecked(False)
        else:
            self.btn_pid.set_playing(self.gw.bluefors.getPIDMode())

        self.btn_manual = PlayPauseButton()
        self.btn_manual.changed.connect(self._handle_btn_change_manual)

        self.status_indicator_manual = LedIndicator(warning=False)
        if not self.exist:
            self.status_indicator_manual.setChecked(False)
        else:
            self.btn_manual.set_playing(self.gw.bluefors.getManualMode())

        ## Status Values
        self.sample_temperature = QLabel()
        self.output_power = QLabel()

        ## Set Boxes

        ### SetPoint
        default_value = 0
        if self.exist:
            default_value = self.gw.bluefors.getSetPoint()*1000
        self.set_point = SpinBox(value=default_value, bounds=[0, 1500])
        self.set_point.valueChanged.connect(self._handle_set_point)
        
        ### Manual Value
        default_value = 0
        if self.exist:
            default_value = self.gw.bluefors.getManualValue()*1000
        self.manual_value = SpinBox(value=default_value, bounds=[0, 1500])
        self.manual_value.valueChanged.connect(self._handle_target_manual_value)

        ### Range
        self.range = QComboBox()
        default_value = 0
        if self.exist:
            default_value = self.gw.bluefors.getRange()
            for i in self.gw.bluefors.possible_ranges:
                self.range.addItem(i)
            self.range.setCurrentIndex(default_value-1)
        self.range.activated.connect(self._handle_range)

        # layout
        layout = QGridLayout()

        layout.addWidget(QLabel("Manual:"), 0, 0)
        layout.addWidget(self.btn_manual, 0, 1)
        layout.addWidget(self.status_indicator_manual, 0, 2)

        layout.addWidget(QLabel("Power: (W)"), 1, 0)
        layout.addWidget(self.output_power, 1, 1, 1, 2)

        layout.addWidget(QLabel("Manual: (W)"), 2, 0)
        layout.addWidget(self.manual_value, 2, 1, 1, 2)
        
        layout.addWidget(QLabel("Range: (W)"), 3, 0)
        layout.addWidget(self.range, 3, 1, 1, 2)

        layout.addWidget(QLabel("PID:"), 0, 3)
        layout.addWidget(self.btn_pid, 0, 4)
        layout.addWidget(self.status_indicator_pid, 0, 5)

        layout.addWidget(QLabel("Sample: (mK)"), 1, 3)
        layout.addWidget(self.sample_temperature, 1, 4, 1, 2)

        layout.addWidget(QLabel("Setpoint: (mK)"), 2, 3)
        layout.addWidget(self.set_point, 2, 4, 1, 2)

        layout.addWidget(QLabel("PID:"), 3, 3)
        layout.addWidget(self.pid_line, 3, 4, 1, 2)

        layout.setColumnStretch(6,6)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)


    ## Button + Status Indicators
    def _handle_status_callback_driver(self, arr):
        logger.debug('%s._handle_status_callback_heating()', self._name)
        pid = bool(arr[0][1])
        manual = bool(arr[0][2])
        self.status_indicator_pid.setChecked(pid)
        self.btn_pid.set_playing(pid)
        self.status_indicator_manual.setChecked(manual)
        self.btn_manual.set_playing(manual)

        self.pid_line.setEnabled(not manual)
        self.set_point.setEnabled(not manual)
        self.btn_pid.setEnabled(not manual)
        self.manual_value.setEnabled(not pid)
        self.btn_manual.setEnabled(not pid)



    @Slot(bool)
    def _handle_btn_change_pid(self, playing:bool):
        logger.debug('%s._handle_btn_change_pid(%s)', self._name, playing)
        self.gw.bluefors.setPIDMode(playing)

    @Slot(bool)
    def _handle_btn_change_manual(self, playing:bool):
        logger.debug('%s._handle_btn_change_manual(%s)', self._name, playing)
        self.gw.bluefors.setManualMode(playing)

    ## Status Values
    def _handle_status_callback_HeaterPower(self, arr):
        logger.debug('%s._handle_status_callback_HeaterPower()', self._name)
        power = arr[0][1]
        self.output_power.setText(f"{power:.2e}")

    def _handle_status_callback_Tsample(self, arr):
        logger.debug('%s._handle_status_callback_Tsample()', self._name)
        temperature = arr[0][1]
        self.sample_temperature.setText(f"{temperature*1000:.1f}")

    ## Set Boxes
    def _handle_set_point(self, value):
        logger.debug('%s._handle_set_point()', self._name)
        self.gw.bluefors.setSetPoint(float(value)/1000)

    def _handle_range(self, value):
        logger.debug('%s._handle_range()', self._name)
        self.gw.bluefors.setRange(value+1)

    def _handle_target_manual_value(self, value):
        logger.debug('%s._handle_target_manual_value()', self._name)
        self.gw.bluefors.setManualValue(float(value))

    def _handle_pid(self, text):
        text = self.pid_line.text()
        li = list(text.split(","))
        try:
            li = np.array(li, dtype = float)
            li = np.concatenate((li, np.array([0,0,0])))
            self.gw.bluefors.setP(float(li[0]))
            self.gw.bluefors.setI(float(li[1]))
            self.gw.bluefors.setD(float(li[2]))
        except ValueError:
            pass
            