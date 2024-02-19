# setup logging
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='GUI_v2.log',
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
    StatusControl,
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
        try:
            adwin = self.gw.adwin.version
            self._check_adwin = True
        except AttributeError:
            self._check_adwin = False

        try:
            femto = self.gw.femto
            self._check_femtos = True
        except:
            self._check_femtos = False

        # try:
        #     bf = self.gw.bluefors
        #     self._check_bluefors = True 
        # except AttributeError:
        #     self._check_bluefors = False
            
        # try:
        #     motor = self.gw.motor
        #     self._check_motor = True
        # except AttributeError:
        #     self._check_motor = False

        # try:
        #     magnet = self.gw.magnet
        #     self._check_magnet = True
        # except AttributeError:
        #     self._check_magnet = False

        # try:
        #     vna = self.gw.vna
        #     self._check_vna = True
        #     self._vna_case = self.gw.vna.case
        # except:
        #     self._check_vna = False


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

        self.measurement_control = MeasurementControl(self.gw)

        if self._check_adwin and self._check_femtos:
            self.sensor_control = AdwinFemtoControl(self.gw)
        else:
            self.sensor_control = None


        # if self._check_adwin:
        #     self.adwin_sensor_control = Adwinv4SensorControl(self.gw)
        # else:
        #     self.adwin_sensor_control = None

        # if self._check_femtos:
        #     self.femto_control = FemtoControl(self.gw)
        # else:
        #     self.femto_control = None
        # if self._check_motor:
        #     self.motor_control = MotorControl(self.gw)
        # else:
        #     self.motor_control = None

        # if self._check_magnet:
        #     self.magnet_control = MagnetControl(self.gw)
        # else:
        #     self.magnet_control = None

        # if self._check_vna:
        #     if self._vna_case == 'time':
        #         self.vna_control = VNATSweepControl(self.gw)
        #     if self._vna_case == 'frequency':
        #         self.vna_control = VNAFSweepControl(self.gw)
        # else:
        #     self.vna_control = None


        self.tabs = PlotTabWidget(self.dgw, plot_form=self.plot_form)

        self.setCentralWidget(self.tabs)

    def init_docks(self):
        """
        Initialize docks
        """
        MIN_DOCK_WIDTH = 100

        self.tree_dock = QDockWidget('Data structure', self)
        self.tree_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        self.tree_dock.setWidget(self.tree_view)

        self.plot_form_dock = QDockWidget('Plot config', self)
        self.plot_form_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        self.plot_form_dock.setWidget(self.plot_form)

        self.measurement_control_dock = QDockWidget('Measurement control', self)
        self.measurement_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        self.measurement_control_dock.setWidget(self.measurement_control)

        if self._check_adwin and self._check_femtos:
            self.sensor_control_dock = QDockWidget('Sensor control', self)
            self.sensor_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
            self.sensor_control_dock.setWidget(self.sensor_control)
        else:
            self.sensor_control_dock = None



        # if self._check_adwin:
        #     self.adwin_sensor_control_dock = QDockWidget('ADwin Sensor Control', self)
        #     self.adwin_sensor_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        #     self.adwin_sensor_control_dock.setWidget(self.adwin_sensor_control)
        # else:
        #     self.adwin_sensor_control_dock = None

        # if self._check_femtos:
        #     self.femto_control_dock = QDockWidget('Femto Control', self)
        #     self.femto_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        #     self.femto_control_dock.setWidget(self.femto_control)
        # else:
        #     self.femto_control_dock = None

        # if self._check_motor:
        #     self.motor_control_dock = QDockWidget('Motor Control', self)
        #     self.motor_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        #     self.motor_control_dock.setWidget(self.motor_control)
        # else:
        #     self.motor_control_dock = None

        # if self._check_magnet:
        #     self.magnet_control_dock = QDockWidget('Magnet Control', self)
        #     self.magnet_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        #     self.magnet_control_dock.setWidget(self.magnet_control)
        # else:
        #     self.magnet_control_dock = None

        # if self._check_vna:
        #     if self._vna_case == 'time':
        #         self.vna_source_control_dock = QDockWidget(f'VNA Control S_{self.gw.vna.S}(t)', self)
        #     if self._vna_case == 'frequency':
        #         self.vna_source_control_dock = QDockWidget(f'VNA Control S_{self.gw.vna.S}(f)', self)
        #     self.vna_source_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
        #     self.vna_source_control_dock.setWidget(self.vna_control)
        # else:
        #     self.vna_source_control_dock = None

        # add dock widgets
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree_dock)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.plot_form_dock)

        self.addDockWidget(Qt.RightDockWidgetArea, self.measurement_control_dock)
        
        if self._check_adwin and self._check_femtos:
            self.addDockWidget(Qt.RightDockWidgetArea, self.sensor_control_dock)

        # if self._check_adwin:
        #     self.addDockWidget(Qt.RightDockWidgetArea, self.adwin_sensor_control_dock)


        # if self._check_femtos:
        #     self.addDockWidget(Qt.RightDockWidgetArea, self.femto_control_dock)
        # if self._check_motor:
        #     self.addDockWidget(Qt.RightDockWidgetArea, self.motor_control_dock)
        # if self._check_magnet:
        #     self.addDockWidget(Qt.RightDockWidgetArea, self.magnet_control_dock)
        # if self._check_vna:
        #     self.addDockWidget(Qt.RightDockWidgetArea, self.vna_source_control_dock)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.plot_form_dock)

        # if self._check_motor and self._check_magnet:
        #     self.splitDockWidget(self.magnet_control_dock, self.motor_control_dock, Qt.Horizontal)
        if self._check_adwin=='v6' and self._check_femtos:
            self.splitDockWidget(self.adwin_sensor_control_dock, self.femto_control_dock, Qt.Horizontal)

        liste=[]
        liste.append(self.tree_dock.toggleViewAction())
        if self._check_adwin == 'v6':
            liste.append(self.adwin_sensor_control_dock.toggleViewAction())
            

        # if self._check_femtos:
        #     liste.append(self.femto_control_dock.toggleViewAction())
        # if self._check_motor:
        #     liste.append(self.motor_control_dock.toggleViewAction())
        # if self._check_magnet:
        #     liste.append(self.magnet_control_dock.toggleViewAction())
        # if self._check_vna:
        #     liste.append(self.vna_source_control_dock.toggleViewAction())
        liste.append(self.plot_form_dock.toggleViewAction())
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
        app.setApplicationName('BlueFors GUI')

        window = BlueForsGUIMainWindow(app, dgw, gw)
        window.show()

        timer = QTimer()
        timer.timeout.connect(window.update)
        timer.start(30)

        sys.exit(app.exec())

