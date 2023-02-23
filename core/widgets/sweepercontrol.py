import threading

from typing import Optional

from qtpy.QtCore import Signal, Slot, Qt
from qtpy.QtWidgets import QGridLayout, QWidget, QToolButton, QStyle, QLineEdit, QHBoxLayout, QVBoxLayout, QFormLayout
from qtpy.QtGui import QDoubleValidator
from pyqtgraph import SpinBox

from p5control import InstrumentGateway
from p5control.gui.widgets.measurementcontrol import StatusIndicator, PlayPauseButton
from p5control.gui import run_async

# from p5control.gui import MonitorValueBox
from qtpy.QtWidgets import QSpinBox, QDoubleSpinBox, QAbstractSpinBox

from core.widgets import SweepControl, OffsetControl
from ..scripts import Sweeper



class SweeperControl(QWidget):
    """
    Widget to control measurements. Lets you run and pause them and change the name.
    """
    stop_signal = Signal()

    def __init__(
        self,
        gw: InstrumentGateway,
        show_selector=True,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self.gw = gw

        self.cont_count = CountController(self)
        self.cont_offset = OffsetControl(self.gw)
        self.cont_sweep = SweepControl(self.gw)

        self.stop_event = threading.Event()
        # self.stop_signal = Signal()
        self._thread = None

        # signals
        self.cont_count.btn.changed.connect(self._handle_btn_change_control)
        self.stop_signal.connect(self._handle_stop_signal)

        # layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.cont_count)
        layout.addWidget(self.cont_offset)
        layout.addWidget(self.cont_sweep)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()

    @Slot(bool)
    def _handle_btn_change_control(self, playing: bool):
        # print("control button: ", playing)
        if playing:
            self.cont_count.sweep_cnt.setEnabled(False)
            self.cont_count.offset_cnt.setEnabled(False)
            self.cont_offset.setEnabled(False)
            self.cont_sweep.setEnabled(False)

            self._thread = threading.Thread(
                target=self._control_thread,
                daemon=True,
                args=[
                    self.stop_event,
                    self.cont_count.offset_cnt.value(),
                    self.cont_count.sweep_cnt.value(),
                ]
            )
            self._thread.start()
        else:
            self.stop_event.set()
            self.cont_count.setEnabled(False)

    def _handle_stop_signal(self):
        self._thread.join()
        self._thread = None
        self.stop_event.clear()

        self.cont_count.sweep_cnt.setEnabled(True)
        self.cont_count.offset_cnt.setEnabled(True)
        self.cont_count.setEnabled(True)
        self.cont_offset.setEnabled(True)
        self.cont_sweep.setEnabled(True)

        self.cont_offset.status_indicator.set_state(False)
        self.cont_sweep.status_indicator.set_state(False)

    def _control_thread(self, stop_event: threading.Event, offset_cnt, sweep_cnt):
        while True:

            self.cont_offset.status_indicator.set_state(True)
            self.cont_sweep.status_indicator.set_state(False)

            for _ in range(offset_cnt):
                if stop_event.is_set():
                    self.stop_signal.emit()
                    return
                self.cont_offset.run_offsets()

            self.cont_offset.status_indicator.set_state(False)
            self.cont_sweep.status_indicator.set_state(True)

            for _ in range(sweep_cnt):
                if stop_event.is_set():
                    self.stop_signal.emit()
                    return
                self.cont_sweep.run_sweeps()

                
class CountController(QWidget):
    def __init__(self, parent: Optional['QWidget'] = None):
        super().__init__(parent)

        # widgets
        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()

        self.offset_cnt = SpinBox(value=1, bounds=[0, 1000], int=True)
        self.sweep_cnt = SpinBox(value=3, bounds=[0, 1000], int=True)

        # signals
        self.btn.changed.connect(self.status_indicator.set_state)

        # layout
        row1_lay = QHBoxLayout()
        row1_lay.addWidget(self.status_indicator)
        row1_lay.addWidget(self.btn)
        row1_lay.addStretch()

        row2_lay = QFormLayout()
        row2_lay.addRow("N offsets", self.offset_cnt)
        row2_lay.addRow("N sweeps", self.sweep_cnt)

        layout = QVBoxLayout(self)
        layout.addLayout(row1_lay)
        layout.addLayout(row2_lay)
        layout.addStretch()