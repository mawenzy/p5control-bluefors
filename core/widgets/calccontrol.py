from typing import Optional

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout

from pyqtgraph import SpinBox

from p5control import InstrumentGateway
from p5control.gui.widgets.measurementcontrol import StatusIndicator, PlayPauseButton

from qtpy.QtWidgets import QComboBox


class CalcControl(QWidget):
    """
    Widget to control Adwin Gold 2 v2
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self.gw = gw

        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()
        self.btn.changed.connect(self.status_indicator.set_state)
        self.btn.changed.connect(self._handle_btn_change)

        self.cv_time = SpinBox(value=self.gw.adwin.cv_time, bounds=[0,10])
        self.cv_time.valueChanged.connect(self._handle_cv_time)
        self.step_size = SpinBox(value=self.gw.calc.step_size, bounds=[1,1000], int=True)
        self.step_size.valueChanged.connect(self._handle_step_size)

        self.bin_stop = SpinBox(value=self.gw.calc.bin_stop, bounds=[0, 1])
        self.bin_stop.valueChanged.connect(self._handle_bin_stop)

        self.bin_points = SpinBox(value=self.gw.calc.bin_points, bounds=[3, 10000], int=True)
        self.bin_points.valueChanged.connect(self._handle_bin_points)

        
        row1_lay = QHBoxLayout()
        row1_lay.addWidget(self.status_indicator)
        row1_lay.addWidget(self.btn)
        row1_lay.addStretch()

        row2_lay = QFormLayout()
        row2_lay.addRow("cv time [s]", self.cv_time)
        row2_lay.addRow("step size", self.step_size)

        row3_lay = QFormLayout()
        row3_lay.addRow('bin stop [V]', self.bin_stop)
        row3_lay.addRow('bin points', self.bin_points)

        layout = QVBoxLayout(self)
        layout.addLayout(row1_lay)
        layout.addLayout(row2_lay)
        layout.addLayout(row3_lay)
        layout.addStretch()

    def _handle_cv_time(self):
        self.gw.adwin.setCVtime(float(self.cv_time.value()))

    def _handle_step_size(self):
        self.gw.calc.setStepSize(int(self.step_size.value()))

    def _handle_bin_stop(self):
        self.gw.calc.setBinStop(float(self.bin_stop.value()))

    def _handle_bin_points(self):
        self.gw.calc.setBinPoints(int(self.bin_points.value()))
        
    @Slot(bool)
    def _handle_btn_change(self, playing: bool):
        self.gw.calc.setRunning(playing)