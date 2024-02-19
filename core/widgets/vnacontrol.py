from typing import Optional

from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QToolButton

from pyqtgraph import SpinBox

from p5control import InstrumentGateway, DataGateway
from .utils import PlayPauseButton, StatusIndicator


from logging import getLogger
logger = getLogger(__name__)


from qtpy.QtWidgets import QComboBox

class DisabledLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setReadOnly(True)

class VNATSweepControl(QWidget):
    """
    Widget to control AMI430
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'VNAControl'

        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        #self.id = self.dgw.register_callback("/status/vna_source", lambda arr: self._handle_status_callback(arr))

        self.status_label = QLabel()
        self.status_label.setText("Output:")
        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()
        self.btn.changed.connect(self._handle_btn_change)

        self.status_label2 = QLabel()
        self.status_label2.setText("Measuring:")
        self.status_indicator2 = StatusIndicator()
        self.btn2 = PlayPauseButton()
        self.btn2.changed.connect(self._handle_btn_change2)

        self.frequency_label = QLabel()
        self.frequency_label.setText("Frequency: (GHz)")
        self.frequency = SpinBox(value=self.gw.vna.getTSweepFrequency()*1e-9, bounds=[0.0001, 40], step=.1)
        self.frequency.valueChanged.connect(self._handle_frequency)

        self.power_label = QLabel()
        self.power_label.setText("Power: (dBm)")
        self.power = SpinBox(value=self.gw.vna.getPower(), bounds=[-30, 10], step=1)
        self.power.valueChanged.connect(self._handle_power)

        self.points_label = QLabel()
        self.points_label.setText("Points:")
        self.points = SpinBox(value=self.gw.vna.getPoints(), bounds=[1, 100001], step=1)
        self.points.valueChanged.connect(self._handle_points)

        self.bandwidth_label = QLabel()
        self.bandwidth_label.setText("Bandwidth: (Hz)")
        self.bandwidth = SpinBox(value=self.gw.vna.getBandwidth(), bounds=[1, 1e6], step=1)
        self.bandwidth.valueChanged.connect(self._handle_bandwidth)

        layout = QGridLayout()

        # layout.setHorizontalSpacing(0)

        layout.addWidget(self.status_label, 0, 0)
        layout.addWidget(self.btn, 0, 1)
        layout.addWidget(self.status_indicator, 0, 2)

        layout.addWidget(self.frequency_label, 1, 0)
        layout.addWidget(self.frequency, 1, 1, 1, 3)

        layout.addWidget(self.power_label, 2, 0)
        layout.addWidget(self.power, 2, 1, 1, 3)
        
        layout.addWidget(self.status_label2, 0, 4)
        layout.addWidget(self.btn2, 0, 5)
        layout.addWidget(self.status_indicator2, 0, 6)

        layout.addWidget(self.points_label, 1, 4)
        layout.addWidget(self.points, 1, 5, 1, 3)

        layout.addWidget(self.bandwidth_label, 2, 4)
        layout.addWidget(self.bandwidth, 2, 5, 1, 3)

        layout.setColumnStretch(8,8)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)

    def _handle_frequency(self):
        logger.debug('%s._handle_frequency()', self._name)
        self.gw.vna.setTSweepFrequency(float(self.frequency.value())*1e9)

    def _handle_power(self):
        logger.debug('%s._handle_power()', self._name)
        self.gw.vna.setPower(float(self.power.value()))

    def _handle_points(self):
        logger.debug('%s._handle_points()', self._name)
        self.gw.vna.setPoints(int(self.points.value()))

    def _handle_bandwidth(self):
        logger.debug('%s._handle_bandwidth()', self._name)
        self.gw.vna.setBandwidth(float(self.bandwidth.value()))

    @Slot(bool)
    def _handle_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        self.gw.vna.setOutput(playing)
        self.status_indicator.set_state(playing)
        self.btn.set_playing(playing)

    @Slot(bool)
    def _handle_btn_change2(self, playing:bool):
        logger.debug('%s._handle_btn_change2(%s)', self._name, playing)
        self.gw.vna.setTSweepMeasuring(playing)
        self.status_indicator2.set_state(playing)
        self.btn2.set_playing(playing)
        self.points.setEnabled(not playing)
        self.bandwidth.setEnabled(not playing)

    # def _handle_status_callback(self, arr):
    #     logger.debug('%s._handle_status_callback()', self._name)
        
    #     output = arr['output'][0]
    #     frequency = arr['frequency'][0]
    #     power = arr['power'][0]
                


class VNAFSweepControl(QWidget):
    """
    Widget to control AMI430
    """
    def __init__(
        self,
        gw: InstrumentGateway,
        parent: Optional['QWidget'] = None
    ):
        super().__init__(parent)

        self._name = 'VNASourceControl'

        self.gw = gw
        self.dgw = DataGateway(allow_callback=True)
        self.dgw.connect()

        self.status_label = QLabel()
        self.status_label.setText('Measuring:')
        self.status_indicator = StatusIndicator()
        self.btn = PlayPauseButton()
        self.btn.changed.connect(self._handle_btn_change)

        self.start_label = QLabel()
        self.start_label.setText("Start: (GHz)")
        self.start = SpinBox(value=self.gw.vna.getFSweepStart()*1e-9, bounds=[0.0001, 40], step=.1)
        self.start.valueChanged.connect(self._handle_start)

        self.stop_label = QLabel()
        self.stop_label.setText("Stop: (GHz)")
        self.stop = SpinBox(value=self.gw.vna.getFSweepStop()*1e-9, bounds=[0.0001, 40], step=.1)
        self.stop.valueChanged.connect(self._handle_stop)

        self.points_label = QLabel()
        self.points_label.setText("Points:")
        self.points = SpinBox(value=self.gw.vna.getPoints(), bounds=[1, 100001], step=1)
        self.points.valueChanged.connect(self._handle_points)

        self.power_label = QLabel()
        self.power_label.setText("Power: (dBm)")
        self.power = SpinBox(value=self.gw.vna.getPower(), bounds=[-30, 10], step=1)
        self.power.valueChanged.connect(self._handle_power)

        self.bandwidth_label = QLabel()
        self.bandwidth_label.setText("Bandwidth: (Hz)")
        self.bandwidth = SpinBox(value=self.gw.vna.getBandwidth(), bounds=[1, 1e6], step=1)
        self.bandwidth.valueChanged.connect(self._handle_bandwidth)
        
        # possible values:   1, 1.5,  2,  3,  5,  7, 10,
        #                  1e1,15e0,2e1,3e1,5e1,7e1,1e2,
        #                  1e2,15e1,2e2,3e2,5e2,7e2,1e3,
        #                  1e3,15e2,2e3,3e3,5e3,7e3,1e4,
        #                  1e4,15e3,2e4,3e4,5e4,7e4,1e5,
        #                  1e5,15e4,2e5,3e5,5e5,7e5,1e6

        self.average_label = QLabel()
        self.average_label.setText("Averages:")
        self.average = SpinBox(value=self.gw.vna.getFSweepAverage(), bounds=[1, 1000], step=1)
        self.average.valueChanged.connect(self._handle_average)
        
        layout = QGridLayout()
        layout.addWidget(self.status_label, 0, 0)
        layout.addWidget(self.btn, 0, 1)
        layout.addWidget(self.status_indicator, 0, 2)

        layout.addWidget(self.start_label, 1, 0)
        layout.addWidget(self.start, 1, 1, 1, 3)

        layout.addWidget(self.stop_label, 2, 0)
        layout.addWidget(self.stop, 2, 1, 1, 3)

        layout.addWidget(self.points_label, 3, 0)
        layout.addWidget(self.points, 3, 1, 1, 3)

        layout.addWidget(self.power_label, 1, 4)
        layout.addWidget(self.power, 1, 5, 1, 3)

        layout.addWidget(self.bandwidth_label, 2, 4)
        layout.addWidget(self.bandwidth, 2, 5, 1, 3)

        layout.addWidget(self.average_label, 3, 4)
        layout.addWidget(self.average, 3, 5, 1, 3)
        
        layout.setColumnStretch(8,8)

        vlayout = QVBoxLayout(self)
        vlayout.addLayout(layout)
        vlayout.addStretch()

        logger.debug('%s initialized.', self._name)

    def _handle_start(self):
        logger.debug('%s._handle_start()', self._name)
        self.gw.vna.setFSweepStart(float(self.start.value())*1e9)

    def _handle_stop(self):
        logger.debug('%s._handle_stop()', self._name)
        self.gw.vna.setFSweepStop(float(self.stop.value())*1e9)

    def _handle_points(self):
        logger.debug('%s._handle_points()', self._name)
        self.gw.vna.setPoints(int(self.points.value()))

    def _handle_power(self):
        logger.debug('%s._handle_power()', self._name)
        self.gw.vna.setPower(float(self.power.value()))

    def _handle_bandwidth(self):
        logger.debug('%s._handle_bandwidth()', self._name)
        self.gw.vna.setBandwidth(float(self.bandwidth.value()))

    def _handle_average(self):
        logger.debug('%s._handle_average()', self._name)
        self.gw.vna.setFSweepAverage(int(self.average.value()))

    @Slot(bool)
    def _handle_btn_change(self, playing:bool):
        logger.debug('%s._handle_btn_change(%s)', self._name, playing)
        self.gw.vna.setOutput(playing)
        self.status_indicator.set_state(playing)
        self.btn.set_playing(playing)
        self.start.setEnabled(not playing)
        self.stop.setEnabled(not playing)
        self.points.setEnabled(not playing)
        self.power.setEnabled(not playing)
        self.bandwidth.setEnabled(not playing)
        self.average.setEnabled(not playing)

