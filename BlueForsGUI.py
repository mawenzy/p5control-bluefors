# setup logging
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='BlueForsGUI.log',
    level=logging.DEBUG,
    filemode='w', # overwrites logs every time this script is started
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(thread)6d %(name)-30s %(funcName)-20s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

import sys

from qtpy.QtCore import (Qt, QTimer, Slot)

from qtpy.QtWidgets import (QMainWindow, QApplication, QDockWidget, QAction, QToolButton)

from qtpy.QtGui import (
    QKeySequence
)

from p5control import (
    InstrumentGateway
)

from p5control.gui import (
    CleanupApp,
    GuiDataGateway,
    DataGatewayTreeView,
    PlotForm,
    PlotTabWidget,
    MeasurementControl
)

from core.widgets import AdwinControl_v2, CalcControl, MotorControl, StatusControl, FemtoControl

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
            adwin = self.gw.adwin
            self._check_adwin = True
        except AttributeError:
            self._check_adwin = False

        try:
            femtos = self.gw.femtos
            self._check_femtos = True
        except:
            self._check_femtos = False

        try:
            calc = self.gw.calc
            self._check_calc = True
        except AttributeError:
            self._check_calc = False

        try:
            bf = self.gw.bluefors
            self._check_bluefors = True 
        except AttributeError:
            self._check_bluefors = False
            
        try:
            motor = self.gw.motor
            self._check_motor = True
        except AttributeError:
            self._check_motor = False

        try:
            magnet = self.gw.magnet
            self._check_magnet = True
        except AttributeError:
            self._check_magnet = False

        try:
            vna = self.gw.vna
            self._check_vna = True
        except AttributeError:
            self._check_vna = False

        try:
            ground = self.gw.ground
            self._check_ground = True
        except AttributeError:
            self._check_ground = True

        try:
            thermo = self.gw.thermo
            self._check_thermo = True
        except:
            self._check_thermo = False


        self._check_status = self._check_bluefors or self._check_thermo or self._check_ground


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

        self.file_menu.addAction(QAction(
            "Refresh",
            self,
            shortcut=QKeySequence.Refresh,
            statusTip='Refresh TreeView',
            triggered=self.handle_refresh
        ))

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

        if self._check_adwin:
            self.adwin_control = AdwinControl_v2(self.gw)
        else:
            self.adwin_control = None

        if self._check_femtos:
            self.femto_control = FemtoControl(self.gw)
        else:
            self.femto_control = None

        if self._check_calc:
            self.calc_control = CalcControl(self.gw)
        else:
            self.calc_control = None

        if self._check_motor:
            self.motor_control = MotorControl(self.gw)
        else:
            self.motor_control = None

        if self._check_status:
            self.status_control = StatusControl(self.gw,
                _check_bluefors = self._check_bluefors,
                _check_thermo = self._check_thermo,
                _check_ground = self._check_ground,
                )
        else:
            self.status_control = None

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

        if self._check_adwin:
            self.adwin_control_dock = QDockWidget('ADwin Control', self)
            self.adwin_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
            self.adwin_control_dock.setWidget(self.adwin_control)
        else:
            self.adwin_control_dock = None
        self.measurement_control_dock.setWidget(self.measurement_control)

        if self._check_femtos:
            self.femto_control_dock = QDockWidget('Femto Control', self)
            self.femto_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
            self.femto_control_dock.setWidget(self.femto_control)
        else:
            self.femto_control_dock = None

        if self._check_calc:
            self.calc_control_dock = QDockWidget('Calc Control', self)
            self.calc_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
            self.calc_control_dock.setWidget(self.calc_control)
        else:
            self.calc_control_dock = None

        if self._check_motor:
            self.motor_control_dock = QDockWidget('Motor Control', self)
            self.motor_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
            self.motor_control_dock.setWidget(self.motor_control)
        else:
            self.motor_control_dock = None

        if self._check_status:
            self.status_control_dock = QDockWidget('Status', self)
            self.status_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
            self.status_control_dock.setWidget(self.status_control)
        else:
            self.status_control_dock = None

        # add dock widgets
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree_dock)

        self.addDockWidget(Qt.RightDockWidgetArea, self.measurement_control_dock)
        
        if self._check_adwin:
            self.addDockWidget(Qt.RightDockWidgetArea, self.adwin_control_dock)
        if self._check_femtos:
            self.addDockWidget(Qt.RightDockWidgetArea, self.femto_control_dock)
        if self._check_calc:
            self.addDockWidget(Qt.RightDockWidgetArea, self.calc_control_dock)

        
        if self._check_motor:
            self.addDockWidget(Qt.RightDockWidgetArea, self.motor_control_dock)
        if self._check_status:
            self.addDockWidget(Qt.RightDockWidgetArea, self.status_control_dock)
            
        # self.addDockWidget(Qt.RightDockWidgetArea, self.plot_form_dock)
        self.splitDockWidget(self.status_control_dock, self.plot_form_dock, Qt.Horizontal)

        # self.view_menu.addActions([
        #     self.tree_dock.toggleViewAction(),
        #     self.measurement_control_dock.toggleViewAction(),
        #     self.adwin_control_dock.toggleViewAction(),
        #     self.calc_control_dock.toggleViewAction(),
        #     self.motor_control_dock.toggleViewAction(),
        #     self.plot_form_dock.toggleViewAction()
        # ])

        liste=[]
        liste.append(self.tree_dock.toggleViewAction())
        if self._check_adwin:
            liste.append(self.adwin_control_dock.toggleViewAction())
        if self._check_femtos:
            liste.append(self.femto_control_dock.toggleViewAction())
        if self._check_calc:
            liste.append(self.calc_control_dock.toggleViewAction())
        if self._check_motor:
            liste.append(self.motor_control_dock.toggleViewAction())
        if self._check_status:
            liste.append(self.status_control_dock.toggleViewAction())
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

