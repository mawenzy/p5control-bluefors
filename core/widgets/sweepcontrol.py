from typing import Optional

from qtpy.QtCore import Signal, Slot, Qt
from qtpy.QtWidgets import QGridLayout, QWidget, QToolButton, QStyle, QLineEdit, QHBoxLayout, QVBoxLayout, QFormLayout
from qtpy.QtGui import QDoubleValidator
from pyqtgraph import SpinBox

from p5control import InstrumentGateway
from p5control.gui.widgets.measurementcontrol import StatusIndicator, PlayPauseButton
from p5control.gui import MonitorValueBox, run_async
from qtpy.QtWidgets import QSpinBox, QDoubleSpinBox, QAbstractSpinBox

from ..scripts import Sweeper

class OffsetControl(QWidget):
    """
    Widget to control measurements. Lets you run and pause them and change the name.
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        show_selector=True,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self.gw = gw

        self.offsets = Sweeper()

        # widgets
        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()
        self.offset_time = SpinBox(value=self.offsets._offset_time, siPrefix=True, bounds=[0, 1000], dec=True, step=1, minStep=0.001)

        # signals
        self.btn.changed.connect(self._handle_btn_change)
        self.btn.changed.connect(self.status_indicator.set_state)

        # layout
        row1_lay = QHBoxLayout()
        row1_lay.addWidget(self.status_indicator)
        row1_lay.addWidget(self.btn)
        row1_lay.addStretch()

        row2_lay = QFormLayout()
        row2_lay.addRow("Offset Time [s]", self.offset_time)

        layout = QVBoxLayout(self)
        layout.addLayout(row1_lay)
        layout.addLayout(row2_lay)
        layout.addStretch()


    @Slot(bool)
    def _handle_btn_change(self, playing: bool):
        if playing:
            # disable button while we handle operation
            self.btn.setEnabled(False)
            self.offset_time.setEnabled(False)

            # this runs the measurement, does not block
            run_async(self.run_offsets, self, callback = lambda: self.btn.set_playing(False))
        else:
            self.btn.setEnabled(True)
            self.offset_time.setEnabled(True)
    
    def run_offsets(self):
        self.offsets._offset_time = self.offset_time.value()

        measure = self.gw.measure()
        self.offsets._hdf5_path = measure.path

        self.offsets.get_offsets()



class SweepControl(QWidget):
    """
    Widget to control measurements. Lets you run and pause them and change the name.
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        show_selector=True,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self.gw = gw

        self.sweep = Sweeper()

        # widgets
        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()

        self.sweep_ampl = SpinBox(value=self.sweep._amplitude, siPrefix=True, bounds=[0, 10], dec=True, step=1, minStep=0.001)
        self.sweep_freq = SpinBox(value=self.sweep._frequency, siPrefix=True, bounds=[0, 5], dec=True, step=1, minStep=0.001)
        self.sweep_count = SpinBox(value=self.sweep._sweep_counts, bounds=[0, 1000], int=True)

        # signals
        self.btn.changed.connect(self.status_indicator.set_state)
        self.btn.changed.connect(self._handle_btn_change)

        # layout
        row1_lay = QHBoxLayout()
        row1_lay.addWidget(self.status_indicator)
        row1_lay.addWidget(self.btn)
        row1_lay.addStretch()

        row2_lay = QFormLayout()
        row2_lay.addRow("Amplitude [V]", self.sweep_ampl)
        row2_lay.addRow("Frequency [Hz]", self.sweep_freq)
        row2_lay.addRow("Sweep Count", self.sweep_count)

        layout = QVBoxLayout(self)
        layout.addLayout(row1_lay)
        layout.addLayout(row2_lay)
        layout.addStretch()

    @Slot(bool)
    def _handle_btn_change(self, playing: bool):
        if playing:
            # disable button while we handle operation
            self.btn.setEnabled(False)
            self.sweep_freq.setEnabled(False)
            self.sweep_ampl.setEnabled(False)
            self.sweep_count.setEnabled(False)

            # this runs the measurement, does not block
            run_async(self.run_sweeps, self, callback = lambda: self.btn.set_playing(False))

        else:
            self.btn.setEnabled(True)
            self.sweep_freq.setEnabled(True)
            self.sweep_ampl.setEnabled(True)
            self.sweep_count.setEnabled(True)

    def run_sweeps(self):
        self.sweep._frequency = self.sweep_freq.value()
        self.sweep._amplitude = self.sweep_ampl.value()
        self.sweep._sweep_counts = self.sweep_count.value()

        measure = self.gw.measure()
        self.sweep._hdf5_path = measure.path

        self.sweep.get_sweeps()