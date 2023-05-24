from typing import Optional

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QGridLayout, QLabel

from pyqtgraph import SpinBox

from p5control import InstrumentGateway, DataGateway
from p5control.gui.widgets.measurementcontrol import StatusIndicator, PlayPauseButton

from qtpy.QtWidgets import QComboBox

from logging import getLogger
logger = getLogger(__name__)

class FemtoControl(QWidget):
    """
    Widget to control FemtoControl
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        self._name = 'FemtoControl'

        self.amps = []
        for i in range(2):
            self.amps.append(QComboBox())
            self.amps[i].addItem('20 db / x10   ')
            self.amps[i].addItem('40 db / x100  ')
            self.amps[i].addItem('60 db / x1000 ')
            self.amps[i].addItem('80 db / x10000')
        self.amps[0].activated.connect(self.onChanged_ch1)
        self.amps[1].activated.connect(self.onChanged_ch2)

        self.status_indicator_A = StatusIndicator()
        self.status_indicator_B = StatusIndicator()

        lay = QGridLayout()
        lay.addWidget(QLabel("Amp(V1):"), 0, 0)
        lay.addWidget(QLabel("Amp(V2):"), 1, 0)

        lay.addWidget(self.amps[0], 0, 1)
        lay.addWidget(self.amps[1], 1, 1)

        lay.addWidget(self.status_indicator_A, 0, 2)
        lay.addWidget(self.status_indicator_B, 1, 2)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(lay)
        vlayout.addStretch()

        self.id = self.dgw.register_callback(
            "/status/femtos", 
            lambda arr: self._handle_status_callback(arr)
            )
        
        # lay.setColumnStretch(1, 1)
        
        logger.debug('%s initialized.', self._name)

    def onChanged_ch1(self, index):
        logger.debug('%s.onChanged_ch1(%i)', self._name, index)
        amps=[10, 100, 1000, 10000]
        self.gw.femtos.set_amplification_A(amps[index])

    def onChanged_ch2(self, index):
        logger.debug('%s.onChanged_ch2(%i)', self._name, index)
        amps=[10, 100, 1000, 10000]
        self.gw.femtos.set_amplification_B(amps[index])

    def _handle_status_callback(self, arr):
        logger.debug('%s._handle_status_callback()', self._name)
        overload_A = not arr['overload_A'][0]
        overload_B = not arr['overload_B'][0]
        self.status_indicator_A.set_state(overload_A)
        self.status_indicator_B.set_state(overload_B)