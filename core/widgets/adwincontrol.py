from typing import Optional

from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout
from pyqtgraph import SpinBox

from p5control import InstrumentGateway
from qtpy.QtWidgets import QComboBox


class AdwinControl(QWidget):
    """
    Widget to control Averaging and Range of Adwin.
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self.gw = gw

        self.averaging = SpinBox(value=self.gw.adwin.averaging, bounds=[1, 100000], int=True)
        self.averaging.valueChanged.connect(self._handle_averaging)

        self.ranges = []
        for i in range(4):
            self.ranges.append(QComboBox())
            self.ranges[i].addItem('10.00')
            self.ranges[i].addItem(' 5.00')
            self.ranges[i].addItem(' 2.50')
            self.ranges[i].addItem(' 1.25')

        self.ranges[0].activated.connect(self.onChanged_ch1)
        self.ranges[1].activated.connect(self.onChanged_ch2)
        self.ranges[2].activated.connect(self.onChanged_ch3)
        self.ranges[3].activated.connect(self.onChanged_ch4)

        row2_lay = QFormLayout()
        row2_lay.addRow("Averaging", self.averaging)
        for i in range(4):
            row2_lay.addRow(f"Range V{i+1}", self.ranges[i])

        layout = QVBoxLayout(self)
        layout.addLayout(row2_lay)
        layout.addStretch()

    def _handle_averaging(self):
        self.gw.adwin.setAveraging(int(self.averaging.value()))

    def onChanged_ch1(self, index):
        ranges=[10, 5, 2.5, 1.25]
        self.gw.adwin.setRange(range=ranges[index], ch=1)

    def onChanged_ch2(self, index):
        ranges=[10, 5, 2.5, 1.25]
        self.gw.adwin.setRange(range=ranges[index], ch=2)

    def onChanged_ch3(self, index):
        ranges=[10, 5, 2.5, 1.25]
        self.gw.adwin.setRange(range=ranges[index], ch=3)

    def onChanged_ch4(self, index):
        ranges=[10, 5, 2.5, 1.25]
        self.gw.adwin.setRange(range=ranges[index], ch=4)