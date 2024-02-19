from typing import Optional

from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QToolButton

from pyqtgraph import SpinBox

from p5control import InstrumentGateway, DataGateway
from .utils import PlayPauseButton, StatusIndicator

import numpy as np
from qtpy.QtWidgets import QComboBox


from logging import getLogger
logger = getLogger(__name__)


# class StatusIndicator(QToolButton):
#     """
#     ``QToolButton``, which indicates a status, with either red or green background color.
#     """
#     def __init__(self):
#         super().__init__()
#         self.setDisabled(True)

#         # start in off state
#         self.state = False
#         self._update_color()

#     def _update_color(self):
#         if self.state:
#             self.setStyleSheet("image: url(Zeichnung.png)")
#         else:
#             self.setIcon(QIcon())

    # def set_state(self, state: bool):
    #     """
    #     Set the state.

    #     Parameters
    #     ----------
    #     state : bool
    #         True -> green, False -> red
    #     """
    #     if self.state == state:
    #         return
    #     self.state = state
    #     self._update_color()

class DisabledLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setReadOnly(True)

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

        self.id = self.dgw.register_callback("/status/adwin", lambda arr: self._handle_status_callback(arr))
        self.id2 = self.dgw.register_callback("/status/rref", lambda arr: self._handle_rref_status_callback(arr))

        self.amps = []
        for i in range(2):
            self.amps.append(QComboBox())
            self.amps[i].addItem('20 db / x10   ')
            self.amps[i].addItem('40 db / x100  ')
            self.amps[i].addItem('60 db / x1000 ')
            self.amps[i].addItem('80 db / x10000')
        self.amps[0].activated.connect(self.onChanged_ch1)
        self.amps[1].activated.connect(self.onChanged_ch2)

        self.V1_off = QLabel()
        self.V2_off = QLabel()

        self.status_indicator_A = StatusIndicator()
        self.status_indicator_B = StatusIndicator()

        self.averaging = SpinBox(value=self.gw.adwin.averaging, bounds=[3, 100000], int=True)
        self.averaging.valueChanged.connect(self._handle_averaging)
        
        self.R_ref = QLabel()

        self.calc_status_indicator = StatusIndicator()
        self.calc_btn = PlayPauseButton()
        self.calc_btn.changed.connect(self._handle_calc_btn_change)
        self.calc_btn.set_playing(self.gw.adwin.getCalculating())

        self.current_threshold = SpinBox(value=self.gw.adwin.getCurrentThreshold(), bounds=[0, 10])
        self.current_threshold.valueChanged.connect(self._handle_current_threshold)

        self.output_status_indicator = StatusIndicator()
        self.output_btn = PlayPauseButton()
        self.output_btn.changed.connect(self._handle_output_btn_change)
        self.output_btn.set_playing(self.gw.adwin.getOutput())

        self.amplitude = SpinBox(value=self.gw.adwin.getAmplitude(), bounds=[0, 10])
        self.amplitude.valueChanged.connect(self._handle_amplitude)
        
        self.sweeping_status_indicator = StatusIndicator()
        self.sweeping_btn = PlayPauseButton()
        self.sweeping_btn.changed.connect(self._handle_sweeping_btn_change)
        self.sweeping_btn.set_playing(self.gw.adwin.getSweeping())

        self.period = SpinBox(value=self.gw.adwin.getPeriod(), bounds=[0, 1000])
        self.period.valueChanged.connect(self._handle_period)

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

        lay.addWidget(QLabel("averaging"), 2, 2)
        lay.addWidget(self.averaging, 2, 3)

        lay.addWidget(QLabel("calculation:"), 3, 0)
        lay.addWidget(self.calc_btn, 3, 1)
        lay.addWidget(self.calc_status_indicator, 3, 4)

        lay.addWidget(QLabel("threshold: (A)"), 3, 2)
        lay.addWidget(self.current_threshold, 3, 3)

        lay.addWidget(QLabel("output:"), 4, 0)
        lay.addWidget(self.output_btn, 4, 1)
        lay.addWidget(self.output_status_indicator, 4, 4)

        lay.addWidget(QLabel("amplitude (V):"), 4, 2)
        lay.addWidget(self.amplitude, 4, 3)

        lay.addWidget(QLabel("sweeping:"), 5, 0)
        lay.addWidget(self.sweeping_btn, 5, 1)
        lay.addWidget(self.sweeping_status_indicator, 5, 4)

        lay.addWidget(QLabel("period /\\: (s)"), 5, 2)
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
        
    def _handle_averaging(self):
        logger.debug('%s._handle_averaging()', self._name)
        self.gw.adwin.setAveraging(int(self.averaging.value()))
        
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

    def _handle_current_threshold(self):
        logger.debug('%s._handle_current_threshold()', self._name)
        self.gw.adwin.setCurrentThreshold(float(self.current_threshold.value()))

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

        self.status_indicator_A.set_state(not arr['V1_ovl'])
        self.status_indicator_B.set_state(not arr['V2_ovl'])

        self.output_status_indicator.set_state(arr['output'])
        self.sweeping_status_indicator.set_state(arr['sweeping'])
        self.calc_status_indicator.set_state(arr['calculating'])

    def _handle_rref_status_callback(self, arr):
        logger.debug('%s._handle_rref_status_callback()', self._name)
        if arr['R_ref'][0] > 1000:
            self.R_ref.setText(f"{arr['R_ref'][0]/1000:.1f}k")
        else:
            self.R_ref.setText(f"{arr['R_ref'][0]:.2f}")



    # def _handle_status_callback(self, arr):
    #     logger.debug('%s._handle_status_callback()', self._name)
    #     overload_A = not arr['overload_A'][0]
    #     overload_B = not arr['overload_B'][0]
    #     self.status_indicator_A.set_state(overload_A)
    #     self.status_indicator_B.set_state(overload_B)