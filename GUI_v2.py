# setup logging
import logging
from time import time
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=f'.data/GUI_v2.log',
    level=logging.DEBUG,
    filemode='w', # overwrites logs every time this script is started
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(thread)6d %(name)-30s %(funcName)-20s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


import sys
sys.path.append('C:\\Users\\BlueFors\\Documents\\p5control\\p5control-bluefors')
sys.path.append('C:\\Users\\BlueFors\\Documents\\p5control')
sys.path.append('C:\\Users\\BlueFors\\Documents')

import sys

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from qtconsole import inprocess

from qtpy.QtCore import (Qt, QTimer, Slot)

from qtpy.QtWidgets import (
    QMainWindow, 
    QApplication, 
    QDockWidget,
    QAction, 
    QToolButton,
    )

from qtpy.QtGui import (
    QKeySequence
)

from p5control import (
    InstrumentGateway,
    DataGateway,
)

from p5control.gui import (
    CleanupApp,
    GuiDataGateway,
    DataGatewayTreeView,
    PlotForm,
    PlotTabWidget,
)



from core.widgets_v2 import (
    MeasurementControl,
    AdwinFemtoControl,
    GateControl,
    VNAControl,
    LockinControl,
    MagnetControl,
    MotorControl,
    HeaterControl,
)

import core.plot

class BlueForsGUIMainWindow(QMainWindow):
    
    def __init__(
        self,
        app: QApplication,
        dgw: GuiDataGateway,
        gw: InstrumentGateway
    ):
        super().__init__()

        self.app = app
        self.dgw = dgw
        self.gw = gw
        
        self.check_instruments()

        self.init_actions()
        self.init_menus()
        self.init_toolbars()
        self.init_statusbar()
        self.init_widgets()
        self.init_docks()
        self.init_signals()


    def check_instruments(self):
        
        ## Add new stuff here!
        try:
            adwin = self.gw.adwin.version
            femto = self.gw.femto
            self._check_sensor = True
        except AttributeError:
            self._check_sensor = False
        try:
            vna = self.gw.vna
            self._check_vna = True
        except AttributeError:
            self._check_vna = False
        try:
            gate = self.gw.gate
            self._check_gate = True
        except AttributeError:
            self._check_gate = False
        try:
            lockin = self.gw.lockin
            self._check_lockin = True
        except AttributeError:
            self._check_lockin = False
        try:
            magnet = self.gw.magnet
            self._check_magnet = True
        except AttributeError:
            self._check_magnet = False
        try:
            motor = self.gw.motor
            self._check_motor = True
        except AttributeError:
            self._check_motor = False
        try:
            bluefors = self.gw.bluefors
            self._check_heater = True
        except AttributeError:
            self._check_heater = False
        ##


    def init_actions(self):
        """
        Initialize actions
        """
        pass

    def init_menus(self):
        """
        Initialize actions
        """
        menu = self.menuBar()

        # file menu
        self.file_menu = menu.addMenu('&File')

        self.file_menu.addAction(
                QAction(
                    "Refresh",
                    self,
                    shortcut=QKeySequence.Refresh,
                    statusTip='Refresh TreeView',
                    triggered=self.handle_refresh,
                )
            )

        # view menu
        self.view_menu = menu.addMenu('&View')

    def init_toolbars(self):
        """
        Initialize toolbars
        """
        pass

    def init_statusbar(self):
        """
        Initialize statusbar
        """
        pass

    def init_widgets(self):
        """
        Initialize widgets
        """
        
        self.tree_view = DataGatewayTreeView(self.dgw)
        self.tree_view.expandAll()

        self.plot_form = PlotForm(self.dgw)
        self.tabs = PlotTabWidget(self.dgw, plot_form=self.plot_form)
        self.setCentralWidget(self.tabs)

        self.measurement_control = MeasurementControl(self.gw)

        ## Add new stuff here!
        self.sensor_control = AdwinFemtoControl(self.gw)
        if not self._check_sensor:
            self.sensor_control.setDisabled(True)

        self.vna_control = VNAControl(self.gw)
        if not self._check_vna:
            self.vna_control.setDisabled(True)

        self.gate_control = GateControl(self.gw)
        if not self._check_gate:
            self.gate_control.setDisabled(True)

        # self.lockin_control = LockinControl(self.gw)
        # if not self._check_lockin:
        #     self.lockin_control.setDisabled(True)

        self.magnet_control = MagnetControl(self.gw)
        if not self._check_magnet:
            self.magnet_control.setDisabled(True)
            
        self.motor_control = MotorControl(self.gw)
        if not self._check_motor:
            self.motor_control.setDisabled(True)
            
        self.heater_control = HeaterControl(self.gw)
        if not self._check_heater:
            self.heater_control.setDisabled(True)
        ##


    def init_docks(self):
        """
        Initialize docks
        """
        MIN_DOCK_WIDTH = 100
        MAX_DOCK_WIDTH = 350

        self.tree_dock = QDockWidget('Data structure', self)
        self.tree_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        # self.tree_dock.setMaximumWidth(MAX_DOCK_WIDTH)
        self.tree_dock.setWidget(self.tree_view)

        self.plot_form_dock = QDockWidget('Plot config', self)
        self.plot_form_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        # self.plot_form_dock.setMaximumWidth(MAX_DOCK_WIDTH)
        self.plot_form_dock.setWidget(self.plot_form)

        self.measurement_control_dock = QDockWidget('Measurement control', self)
        self.measurement_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        self.measurement_control_dock.setMaximumWidth(MAX_DOCK_WIDTH)
        self.measurement_control_dock.setWidget(self.measurement_control)

        ## Add new stuff here!
        self.sensor_control_dock = QDockWidget('Sensor control', self)
        self.sensor_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        self.sensor_control_dock.setMaximumWidth(MAX_DOCK_WIDTH)
        self.sensor_control_dock.setWidget(self.sensor_control)

        self.vna_control_dock = QDockWidget('VNA control', self)
        self.vna_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        self.vna_control_dock.setMaximumWidth(MAX_DOCK_WIDTH)
        self.vna_control_dock.setWidget(self.vna_control)
        
        self.gate_control_dock = QDockWidget('Gate control', self)
        self.gate_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        self.gate_control_dock.setMaximumWidth(MAX_DOCK_WIDTH)
        self.gate_control_dock.setWidget(self.gate_control)

        # self.lockin_control_dock = QDockWidget('Lockin control', self)
        # self.lockin_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        # self.lockin_control_dock.setWidget(self.lockin_control)

        self.magnet_control_dock = QDockWidget('Magnet control', self)
        self.magnet_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        self.magnet_control_dock.setMaximumWidth(MAX_DOCK_WIDTH)
        self.magnet_control_dock.setWidget(self.magnet_control)

        self.motor_control_dock = QDockWidget('Motor control', self)
        self.motor_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        self.motor_control_dock.setMaximumWidth(MAX_DOCK_WIDTH)
        self.motor_control_dock.setWidget(self.motor_control)

        self.heater_control_dock = QDockWidget('Heater control', self)
        self.heater_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        self.heater_control_dock.setMaximumWidth(MAX_DOCK_WIDTH)
        self.heater_control_dock.setWidget(self.heater_control)
        ##

        liste=[]
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree_dock)
        liste.append(self.tree_dock.toggleViewAction())

        self.addDockWidget(Qt.LeftDockWidgetArea, self.plot_form_dock)
        liste.append(self.plot_form_dock.toggleViewAction())

        self.addDockWidget(Qt.RightDockWidgetArea, self.measurement_control_dock)
        
        ## Add new stuff here!
        self.addDockWidget(Qt.RightDockWidgetArea, self.sensor_control_dock)
        liste.append(self.sensor_control_dock.toggleViewAction())

        self.addDockWidget(Qt.RightDockWidgetArea, self.vna_control_dock)
        liste.append(self.vna_control_dock.toggleViewAction())
        self.addDockWidget(Qt.RightDockWidgetArea, self.gate_control_dock)
        liste.append(self.gate_control_dock.toggleViewAction())

        self.addDockWidget(Qt.RightDockWidgetArea, self.magnet_control_dock)
        liste.append(self.magnet_control_dock.toggleViewAction())
        self.addDockWidget(Qt.RightDockWidgetArea, self.motor_control_dock)
        liste.append(self.motor_control_dock.toggleViewAction())

        self.addDockWidget(Qt.RightDockWidgetArea, self.heater_control_dock)
        liste.append(self.heater_control_dock.toggleViewAction())
        # self.addDockWidget(Qt.RightDockWidgetArea, self.lockin_control_dock)
        # liste.append(self.lockin_control_dock.toggleViewAction())

        self.splitDockWidget(self.vna_control_dock, self.gate_control_dock, Qt.Horizontal)
        # self.splitDockWidget(self.heater_control_dock, self.lockin_control_dock, Qt.Horizontal)
        # self.splitDockWidget(self.heater_control_dock, self.magnet_control_dock, Qt.Horizontal)
        self.splitDockWidget(self.magnet_control_dock, self.motor_control_dock, Qt.Horizontal)
        
        # self.splitDockWidget(self.gate_control_dock, self.lockin_control_dock, Qt.Horizontal)

        ##

        self.view_menu.addActions(liste)

    def init_signals(self):
        """
        Initialize signals
        """
        self.tree_view.doubleClickedDataset.connect(self.tabs.plot_path)

    @Slot()
    def handle_refresh(self):
        self.tree_view.update_data()

    def update(self):
        self.tabs.currentWidget().update()
        
if __name__ == '__main__':
    with GuiDataGateway(allow_callback=True) as dgw, InstrumentGateway() as gw:

        app = CleanupApp()
        app.setOrganizationName('P5-Control-Team')
        app.setApplicationName('BlueFors GUI v2')

        window = BlueForsGUIMainWindow(app, dgw, gw)
        window.show()

        timer = QTimer()
        timer.timeout.connect(window.update)
        timer.start(30)

        sys.exit(app.exec())

