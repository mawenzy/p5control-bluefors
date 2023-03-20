from typing import Optional

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout

from pyqtgraph import SpinBox

from p5control import InstrumentGateway
from p5control.gui.widgets.measurementcontrol import StatusIndicator, PlayPauseButton

from qtpy.QtWidgets import QComboBox


class AddawinControl(QWidget):
    """
    Widget to control Averaging and Range of addawin.
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self.gw = gw

        self.averaging = SpinBox(value=self.gw.addawin.averaging, bounds=[1, 100000], int=True)
        self.averaging.valueChanged.connect(self._handle_averaging)

        self.ranges = []
        for i in range(2):
            self.ranges.append(QComboBox())
            self.ranges[i].addItem('10.00')
            self.ranges[i].addItem(' 5.00')
            self.ranges[i].addItem(' 2.50')
            self.ranges[i].addItem(' 1.25')
        self.ranges[0].activated.connect(self.onChanged_ch1)
        self.ranges[1].activated.connect(self.onChanged_ch2)

        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()
        
        self.btn.changed.connect(self._handle_btn_change)
        self.btn.changed.connect(self.status_indicator.set_state)

        self.amplitude = SpinBox(value=self.gw.addawin.amplitude, bounds=[0,10])
        self.frequency = SpinBox(value=self.gw.addawin.frequency, bounds=[0,100])
        self.lockin_amplitude = SpinBox(value=self.gw.addawin.lockin_amplitude, bounds=[0,10])
        self.lockin_frequency = SpinBox(value=self.gw.addawin.lockin_frequency, bounds=[0,10000])
        
        self.amplitude.valueChanged.connect(self._handle_amplitude)
        self.frequency.valueChanged.connect(self._handle_frequency)
        self.lockin_amplitude.valueChanged.connect(self._handle_lockin_amplitude)
        self.lockin_frequency.valueChanged.connect(self._handle_lockin_frequency)

        row1_lay = QFormLayout()
        row1_lay.addRow("Averaging", self.averaging)
        for i in range(2):
            row1_lay.addRow(f"Range V{i+1}", self.ranges[i])
        
        row2_lay = QHBoxLayout()
        row2_lay.addWidget(self.status_indicator)
        row2_lay.addWidget(self.btn)
        row2_lay.addStretch()

        row3_lay = QFormLayout()
        row3_lay.addRow("sweep: A (V)", self.amplitude)
        row3_lay.addRow("sweep: f (Hz)", self.frequency)
        row3_lay.addRow("lockin: A (V)", self.lockin_amplitude)
        row3_lay.addRow("lockin: f (Hz)", self.lockin_frequency)
        row2_lay.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(row1_lay)
        layout.addLayout(row2_lay)
        layout.addLayout(row3_lay)
        layout.addStretch()

    def _handle_averaging(self):
        self.gw.addawin.setAveraging(int(self.averaging.value()))

    def onChanged_ch1(self, index):
        ranges=[10, 5, 2.5, 1.25]
        self.gw.addawin.setRange(range=ranges[index], ch=1)

    def onChanged_ch2(self, index):
        ranges=[10, 5, 2.5, 1.25]
        self.gw.addawin.setRange(range=ranges[index], ch=2)

    def _handle_amplitude(self):
        self.gw.addawin.setAmplitude(float(self.amplitude.value()))

    def _handle_frequency(self):
        self.gw.addawin.setFrequency(float(self.frequency.value()))

    def _handle_lockin_amplitude(self):
        self.gw.addawin.setLockinAmplitude(float(self.lockin_amplitude.value()))

    def _handle_lockin_frequency(self):
        self.gw.addawin.setLockinFrequency(float(self.lockin_frequency.value()))
        
    @Slot(bool)
    def _handle_btn_change(self, playing: bool):
        self.gw.addawin.setSweeping(playing)