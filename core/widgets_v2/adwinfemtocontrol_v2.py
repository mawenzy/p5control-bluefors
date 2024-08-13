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
class AdwinFemtoControl(QWidget):
    """
    Widget to control Adwin Sensory Unit
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'AdwinFemtoControl'
        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        self.exist = True
        try:
            a = self.gw.adwin
        except AttributeError:
            self.exist = False

        self.femto_exist = True
        try:
            a = self.gw.femto
        except AttributeError:
            self.femto_exist = False

        if self.exist:
            self.id = self.dgw.register_callback("/status/adwin", lambda arr: self._handle_status_callback(arr))
            self.id2 = self.dgw.register_callback("/status/rref", lambda arr: self._handle_rref_status_callback(arr))

        self.amps = []
        items = ['20 db / x10   ', '40 db / x100  ', '60 db / x1000 ', '80 db / x10000']
        items = ['x10   ', 'x100  ', 'x1000 ', 'x10000']
        handlers = [self.onChanged_ch1, self.onChanged_ch2]
        channels = ['A', 'B']
        for i in range(2):
            self.amps.append(QComboBox())
            for item in items:
                self.amps[i].addItem(item)
            self.amps[i].activated.connect(handlers[i])
            default_value = 0
            if self.femto_exist:
                default_value = self.gw.femto.get_amp(channels[i])
            self.amps[i].setCurrentIndex(int(np.log10(default_value))-1)

        self.V1_off = QLabel()
        self.V2_off = QLabel()

        self.status_indicator_A = LedIndicator(warning=True)
        self.status_indicator_B = LedIndicator(warning=True)

        default_value = 0
        if self.exist:
            default_value = self.gw.adwin.sample_rate
        self.sample_rate = SpinBox(value=default_value, bounds=[1, 5e4], int=False)
        self.sample_rate.valueChanged.connect(self._handle_sample_rate)
        
        self.R_ref = QLabel()

        self.calc_status_indicator = LedIndicator()
        self.calc_btn = PlayPauseButton()
        self.calc_btn.changed.connect(self._handle_calc_btn_change)
        if self.exist:
            self.calc_btn.set_playing(self.gw.adwin.getCalculating())

        default_value = 0
        if self.exist:
            default_value = self.gw.adwin.getSeriesResistance()
        self.series_resistance = SpinBox(value=default_value, bounds=[0, 6e8])
        self.series_resistance.valueChanged.connect(self._handle_series_resistance)

        self.output_status_indicator = LedIndicator()
        self.output_btn = PlayPauseButton()
        self.output_btn.changed.connect(self._handle_output_btn_change)
        if self.exist:
            self.output_btn.set_playing(self.gw.adwin.getOutput())

        default_value = 0
        if self.exist:
            default_value = self.gw.adwin.getAmplitude()
        self.amplitude = SpinBox(value=default_value, bounds=[0, 10])
        self.amplitude.valueChanged.connect(self._handle_amplitude)
        
        self.sweeping_status_indicator = LedIndicator()
        self.sweeping_btn = PlayPauseButton()
        self.sweeping_btn.changed.connect(self._handle_sweeping_btn_change)
        if self.exist:
            self.sweeping_btn.set_playing(self.gw.adwin.getSweeping())

        default_value = 0
        if self.exist:
            default_value = self.gw.adwin.getPeriod()
        self.period = SpinBox(value=default_value, bounds=[0, 1000])
        self.period.valueChanged.connect(self._handle_period)

        if not self.exist:
            self.status_indicator_A.set_disabled()
            self.status_indicator_B.set_disabled()
            self.calc_status_indicator.set_disabled()
            self.output_status_indicator.set_disabled()
            self.sweeping_status_indicator.set_disabled()

        lay = QGridLayout()

        lay.addWidget(QLabel("off V1 (V):"), 0, 0)
        lay.addWidget(QLabel("off V2 (V):"), 1, 0)
        
        lay.addWidget(self.V1_off, 0, 1)
        lay.addWidget(self.V2_off, 1, 1)

        lay.addWidget(QLabel("amp V1:"), 0, 2)
        lay.addWidget(QLabel("amp V2:"), 1, 2)

        lay.addWidget(self.amps[0], 0, 3)
        lay.addWidget(self.amps[1], 1, 3)

        lay.addWidget(self.status_indicator_A, 0, 4)
        lay.addWidget(self.status_indicator_B, 1, 4)

        lay.addWidget(QLabel("Rref (Ohm):"), 2, 0)
        lay.addWidget(self.R_ref, 2, 1)

        lay.addWidget(QLabel("Sample Rate: (Hz)"), 2, 2)
        lay.addWidget(self.sample_rate, 2, 3)

        lay.addWidget(QLabel("Calculation:"), 3, 0)
        lay.addWidget(self.calc_btn, 3, 1)
        lay.addWidget(self.calc_status_indicator, 3, 4)

        lay.addWidget(QLabel("R_series: (Ohm)"), 3, 2)
        lay.addWidget(self.series_resistance, 3, 3)

        lay.addWidget(QLabel("Output:"), 4, 0)
        lay.addWidget(self.output_btn, 4, 1)
        lay.addWidget(self.output_status_indicator, 4, 4)

        lay.addWidget(QLabel("Amplitude: (V)"), 4, 2)
        lay.addWidget(self.amplitude, 4, 3)

        lay.addWidget(QLabel("Sweeping:"), 5, 0)
        lay.addWidget(self.sweeping_btn, 5, 1)
        lay.addWidget(self.sweeping_status_indicator, 5, 4)

        lay.addWidget(QLabel("Period XX: (s)"), 5, 2)
        lay.addWidget(self.period, 5, 3)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(lay)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)

    @Slot(bool)

    def onChanged_ch1(self, index):
        logger.debug('%s.onChanged_ch1(%i)', self._name, index)
        amps=[10, 100, 1000, 10000]
        self.gw.femto.set_amp(amps[index], 'A')

    def onChanged_ch2(self, index):
        logger.debug('%s.onChanged_ch2(%i)', self._name, index)
        amps=[10, 100, 1000, 10000]
        self.gw.femto.set_amp(amps[index], 'B')
        
    def _handle_sample_rate(self):
        logger.debug('%s._handle_sample_rate()', self._name)
        self.gw.adwin.setSampleRate(int(self.sample_rate.value()))
        
    def _handle_output_btn_change(self, playing:bool):
        logger.debug('%s._handle_output_btn_change(%s)', self._name, playing)
        self.gw.adwin.setOutput(playing)

    def _handle_amplitude(self):
        logger.debug('%s._handle_amplitude()', self._name)
        self.gw.adwin.setAmplitude(float(self.amplitude.value()))

    def _handle_sweeping_btn_change(self, playing:bool):
        logger.debug('%s._handle_sweeping_btn_change(%s)', self._name, playing)
        self.gw.adwin.setSweeping(playing)

    def _handle_period(self):
        logger.debug('%s._handle_period()', self._name)
        self.gw.adwin.setPeriod(float(self.period.value()))

    def _handle_calc_btn_change(self, playing:bool):
        logger.debug('%s._handle_calc_btn_change(%s)', self._name, playing)
        self.gw.adwin.setCalculating(playing)

    def _handle_series_resistance(self):
        logger.debug('%s._handle_series_resistance()', self._name)
        self.gw.adwin.setSeriesResistance(float(self.series_resistance.value()))

    def _handle_status_callback(self, arr):
        logger.debug('%s._handle_status_callback()', self._name)
        if arr['V1_off'][0] < 1:
            self.V1_off.setText(f"{float(arr['V1_off'][0]*1000):3.1f}m")
        else:
            self.V1_off.setText(f"{arr['V1_off'][0]:3.2f}")

        if arr['V2_off'][0] < 1:
            self.V2_off.setText(f"{float(arr['V2_off'][0]*1000):3.1f}m")
        else:
            self.V2_off.setText(f"{arr['V2_off'][0]:3.2f}")

        self.status_indicator_A.setChecked(not arr['V1_ovl'])
        self.status_indicator_B.setChecked(not arr['V2_ovl'])

        self.output_status_indicator.setChecked(arr['output'][0])
        self.sweeping_status_indicator.setChecked(arr['sweeping'][0])
        self.calc_status_indicator.setChecked(arr['calculating'][0])

    def _handle_rref_status_callback(self, arr):
        logger.debug('%s._handle_rref_status_callback()', self._name)
        if arr['R_ref'][0] > 1000:
            self.R_ref.setText(f"{arr['R_ref'][0]/1000:.1f}k")
        else:
            self.R_ref.setText(f"{arr['R_ref'][0]:.2f}")