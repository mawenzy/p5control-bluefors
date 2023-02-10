from typing import Optional

from qtpy.QtCore import Signal, Slot, Qt
from qtpy.QtWidgets import QGridLayout, QWidget, QToolButton, QStyle, QLineEdit, QHBoxLayout, QVBoxLayout, QFormLayout
from qtpy.QtGui import QDoubleValidator
from pyqtgraph import SpinBox

from p5control import InstrumentGateway
from p5control.gui.widgets.measurementcontrol import StatusIndicator, PlayPauseButton

from p5control.gui import MonitorValueBox
from qtpy.QtWidgets import QSpinBox, QDoubleSpinBox, QAbstractSpinBox

from ..scripts import Offsets, Sweeps

class SweeperControl(QWidget):
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
        self.sweeps = Sweeps()
        self.offsets = Offsets()

        # widgets
        self.status_indicator_control = StatusIndicator()
        self.btn_control = PlayPauseButton()
        
        self.status_indicator_offset = StatusIndicator()
        self.btn_offset = PlayPauseButton()

        self.status_indicator_sweeps = StatusIndicator()
        self.btn_sweeps = PlayPauseButton()
        
        self.control_offset = SpinBox(value=1, bounds=[0, 1000], int=True)
        self.control_sweeps = SpinBox(value=3, bounds=[0, 1000], int=True)

        self.offset_time = SpinBox(value=self.offsets._offset_time, siPrefix=True, bounds=[0, 1000], dec=True, step=1, minStep=0.001)
        self.sweep_ampl = SpinBox(value=self.sweeps._amplitude, siPrefix=True, bounds=[0, 5], dec=True, step=1, minStep=0.001)
        self.sweep_freq = SpinBox(value=self.sweeps._frequency, siPrefix=True, bounds=[0, 5], dec=True, step=1, minStep=0.001)
        self.sweep_count = SpinBox(value=self.sweeps._sweep_counts, bounds=[0, 1000], int=True)

        # signals
        self.btn_control.changed.connect(self._handle_btn_change_control)
        self.btn_control.changed.connect(self.status_indicator_control.set_state)
        self.offsets.finished.connect(lambda: self.btn_control.set_playing(False))
        self.sweeps.finished.connect(lambda: self.btn_control.set_playing(False))
        
        self.btn_offset.changed.connect(self._handle_btn_change_offset)
        self.btn_offset.changed.connect(self.status_indicator_offset.set_state)
        self.offsets.finished.connect(lambda: self.btn_offset.set_playing(False))
        
        self.btn_sweeps.changed.connect(self._handle_btn_change_sweeps)
        self.btn_sweeps.changed.connect(self.status_indicator_sweeps.set_state)
        self.sweeps.finished.connect(lambda: self.btn_sweeps.set_playing(False))

        # layout
        row0a_lay = QHBoxLayout()
        row0a_lay.addWidget(self.status_indicator_control)
        row0a_lay.addWidget(self.btn_control)
        row0a_lay.addStretch()

        row0b_lay = QFormLayout()
        row0b_lay.addRow("N offsets", self.control_offset)
        row0b_lay.addRow("N sweeps", self.control_sweeps)

        row1_lay = QHBoxLayout()
        row1_lay.addWidget(self.status_indicator_offset)
        row1_lay.addWidget(self.btn_offset)
        row1_lay.addStretch()

        row2_lay = QFormLayout()
        row2_lay.addRow("Offset Time [s]", self.offset_time)
        
        row3_lay = QHBoxLayout()
        row3_lay.addWidget(self.status_indicator_sweeps)
        row3_lay.addWidget(self.btn_sweeps)
        row3_lay.addStretch()

        row4_lay = QFormLayout()
        row4_lay.addRow("Amplitude [V]", self.sweep_ampl)
        row4_lay.addRow("Frequency [Hz]", self.sweep_freq)
        row4_lay.addRow("Sweep Count", self.sweep_count)

        layout = QVBoxLayout(self)
        layout.addLayout(row0a_lay)
        layout.addLayout(row0b_lay)
        layout.addLayout(row1_lay)
        layout.addLayout(row2_lay)
        layout.addLayout(row3_lay)
        layout.addLayout(row4_lay)
        layout.addStretch()


    @Slot(bool)
    def _handle_btn_change_offset(self, playing_offset: bool):
        if playing_offset:
            # disable button while we handle operation
            self.btn_offset.setEnabled(False)
            self.offset_time.setEnabled(False)

            self.offsets._offset_time = self.offset_time.value()

            measure = self.gw.measure()
            self.offsets._hdf5_path = measure.path()

            # this runs the measurement, does not block
            self.offsets.start()
        else:
            self.btn_offset.setEnabled(True)
            self.offset_time.setEnabled(True)

    @Slot(bool)
    def _handle_btn_change_sweeps(self, playing_sweep: bool):
        if playing_sweep:
            # disable button while we handle operation
            self.btn_sweeps.setEnabled(False)
            self.sweep_freq.setEnabled(False)
            self.sweep_ampl.setEnabled(False)
            self.sweep_count.setEnabled(False)

            freq = self.sweep_freq.value()
            ampl = self.sweep_ampl.value()
            count = self.sweep_count.value()

            self.sweeps._frequency = freq
            self.sweeps._amplitude = ampl
            self.sweeps._sweep_counts = count

            measure = self.gw.measure()
            self.sweeps._hdf5_path = measure.path()

            # this runs the measurement, does not block
            self.sweeps.start()

        else:
            self.btn_sweeps.setEnabled(True)
            self.sweep_freq.setEnabled(True)
            self.sweep_ampl.setEnabled(True)
            self.sweep_count.setEnabled(True)


    @Slot(bool)
    def _handle_btn_change_control(self, playing_control: bool):
        if playing_control:
            self.control_offset.setEnabled(False)
            self.control_sweeps.setEnabled(False)
            self._handle_btn_change_offset(True)
            self._handle_btn_change_sweeps(True)
        else:
            self.control_offset.setEnabled(True)
            self.control_sweeps.setEnabled(True)
