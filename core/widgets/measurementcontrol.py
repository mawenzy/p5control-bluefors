from typing import Optional

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QGridLayout, QWidget, QLineEdit, QVBoxLayout, QLabel

from p5control import InstrumentGateway

from .utils import PlayPauseButton, StatusIndicator

class MeasurementControl(QWidget):
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

        # widgets
        self.status_label = QLabel()
        self.status_label.setText("Run:")
        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()

        self.name_label = QLabel()
        self.name_label.setText("Name:")
        self.name = QLineEdit()

        self.btn.changed.connect(self._handle_btn_change)
        # couple status indicator to btn
        self.btn.changed.connect(self.status_indicator.set_state)

        # layout
        layout = QGridLayout()
        layout.addWidget(self.status_label, 0, 0)
        layout.addWidget(self.btn, 0, 1)
        layout.addWidget(self.status_indicator, 0, 2)
        layout.addWidget(self.name_label, 1, 0)
        layout.addWidget(self.name, 1, 1, 1, 2)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        layout.setColumnStretch(3,3)

        # get first measurement
        self.gw_update()

    @Slot(bool)
    def _handle_btn_change(self, playing: bool):
        # disable button while we handle operation
        self.btn.setEnabled(False)

        # disable line edit when measurement is running
        if playing:
            self.name.setEnabled(False)
        else:
            self.name.setEnabled(True)

        measure = self.gw.measure(self.name.text())
        if playing and not measure.running:
            measure.start()
        elif not playing and measure.running:
            measure.stop()

        self.btn.setEnabled(True)

    def gw_update(self):
        """
        Update the widget by requesting the Measurement object from the instrument server and
        reading its state into this widget.
        """
        measure = self.gw.measure()
        self.last_name = measure.name

        self.name.setText(measure.name)
        self.btn.set_playing(measure.running)
