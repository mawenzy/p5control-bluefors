from typing import Optional

from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout

from pyqtgraph import SpinBox

from p5control import InstrumentGateway, DataGateway
from p5control.gui.widgets.measurementcontrol import StatusIndicator, PlayPauseButton
from core.utilities.config import dump_to_config, load_from_config

from qtpy.QtWidgets import QComboBox


from logging import getLogger
logger = getLogger(__name__)

class DisabledLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setReadOnly(True)

class StatusControl(QWidget):
    """
    Widget to show status values
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None,
        _check_bluefors = False,
        _check_thermo = False,
        _check_ground = False,
    ):
        super().__init__(parent)

        self._name = 'StatusControl'

        self._check_bluefors = _check_bluefors
        self._check_thermo = _check_thermo
        self._check_ground = _check_ground

        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        lay = QFormLayout()

        layout = QGridLayout()
        i = 0

        if self._check_bluefors:
            self.bluefors = DisabledLineEdit()
            self.bluefors_label = QLabel()
            self.bluefors_label.setText('Sample T (mK)')
            layout.addWidget(self.bluefors_label, i, 0)
            layout.addWidget(self.bluefors, i, 1)
            i += 1
            id_bluefors = self.dgw.register_callback(
                "/status/bluefors/temperature/MCBJ",
                  lambda arr: self._handle_bluefors_status_callback(arr)
                  )

        if self._check_thermo:
            self.thermo = DisabledLineEdit()
            self.thermo_label = QLabel()
            self.thermo_label.setText('Lab T (°C)')
            layout.addWidget(self.thermo_label, i, 0)
            layout.addWidget(self.thermo, i, 1)
            i += 1
            id_thermo = self.dgw.register_callback(
                "/status/thermo", 
                lambda arr: self._handle_thermo_status_callback(arr)
                )
        
        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)


    def _handle_bluefors_status_callback(self, arr):
        logger.debug('%s._handle_bluefors_status_callback()', self._name)
        T = arr['T'][0]
        self.bluefors.setText(f"{T*1000:.1f}")

    def _handle_thermo_status_callback(self, arr):
        logger.debug('%s._handle_thermo_status_callback()', self._name)
        T = arr['T'][0]
        self.thermo.setText(f"{T:.2f}")
