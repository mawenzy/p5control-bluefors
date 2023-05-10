from typing import Optional

from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QLineEdit

from pyqtgraph import SpinBox

from p5control import InstrumentGateway, DataGateway
from p5control.gui.widgets.measurementcontrol import StatusIndicator, PlayPauseButton
from core.utilities.config import dump_to_config, load_from_config

from qtpy.QtWidgets import QComboBox

class DisabledLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setDisabled(True)

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

        self._check_bluefors = _check_bluefors
        self._check_thermo = _check_thermo
        self._check_ground = _check_ground

        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        lay = QFormLayout(self)

        if self._check_bluefors:
            id = self.dgw.register_callback("/status/bluefors/LakeShore370AC/MCBJ", lambda arr: self._handle_bluefors_status_callback(arr))
            self.bluefors_label = DisabledLineEdit()
            lay.addRow("Sample", self.bluefors_label)

        if self._check_thermo:
            id = self.dgw.register_callback("/status/thermo", lambda arr: self._handle_thermo_status_callback(arr))
            self.thermo_label = DisabledLineEdit()
            lay.addRow("Ground separation", self.thermo_label)

        if self._check_ground:
            id = self.dgw.register_callback("/status/ground", lambda arr: self._handle_ground_status_callback(arr))
            self.ground_label = DisabledLineEdit()
            lay.addRow("Laboratory", self.ground_label)
        

    def _handle_bluefors_status_callback(self, arr):
        T = arr['T'][0]
        self.bluefors_label.setText(f"T = {T:.2f} K")

    def _handle_ground_status_callback(self, arr):
        R = arr['R'][0]
        self.ground_label.setText(f"R = {R/1000:.1f} kOhm")

    def _handle_thermo_status_callback(self, arr):
        T = arr['T'][0]
        self.thermo_label.setText(f"T = {T:.2f} °C")
