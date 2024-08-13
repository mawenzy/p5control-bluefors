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

from core.widgets import (
    MeasurementControl,
    MotorControl, 
    StatusControl, 
    FemtoControl, 
    MagnetControl, 
    VNAFSweepControl, 
    VNATSweepControl, 
    AdwinControl_v5,
    SourceControl_v2,
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
            ground = self.gw.ground
            self._check_ground = True
        except AttributeError:
            self._check_ground = True

        try:
            thermo = self.gw.thermo
            self._check_thermo = True
        except:
            self._check_thermo = False

        try:
            vna = self.gw.vna
            self._check_vna = True
            self._vna_case = self.gw.vna.case
        except:
            self._check_vna = False

        try:
            source = self.gw.source
            self._check_source = True
        except:
            self._check_source = False

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


        if self._check_adwin:
            self.adwin_control = AdwinControl_v5(self.gw)
        else:
            self._check_adwin = None

        if self._check_femtos:
            self.femto_control = FemtoControl(self.gw)
        else:
            self.femto_control = None

        if self._check_source:
            self.source_control = SourceControl_v2(self.gw)
        else:
            self.source_control = None

        if self._check_motor:
            self.motor_control = MotorControl(self.gw)
        else:
            self.motor_control = None

        if self._check_magnet:
            self.magnet_control = MagnetControl(self.gw)
        else:
            self.magnet_control = None

        if self._check_vna:
            if self._vna_case == 'time':
                self.vna_control = VNATSweepControl(self.gw)
            if self._vna_case == 'frequency':
                self.vna_control = VNAFSweepControl(self.gw)
        else:
            self.vna_control = None

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

        self.jupyter_console_control = JupyterConsoleWidget()
        self.jupyter_console_control_dock = QDockWidget("Jupyter Console Dock", self)
        self.jupyter_console_control_dock.setWidget(self.jupyter_console_control)

        if self._check_adwin:
            self.adwin_control_dock = QDockWidget('ADwin Control', self)
            self.adwin_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
            self.adwin_control_dock.setWidget(self.adwin_control)
        else:
            self.adwin_control_dock = None

        if self._check_femtos:
            self.femto_control_dock = QDockWidget('Femto Control', self)
            self.femto_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
            self.femto_control_dock.setWidget(self.femto_control)
        else:
            self.femto_control_dock = None

        if self._check_source:
            self.source_control_dock = QDockWidget('Source Control', self)
            self.source_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
            self.source_control_dock.setWidget(self.source_control)
        else:
            self.source_control_dock = None

        if self._check_motor:
            self.motor_control_dock = QDockWidget('Motor Control', self)
            self.motor_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
            self.motor_control_dock.setWidget(self.motor_control)
        else:
            self.motor_control_dock = None

        if self._check_magnet:
            self.magnet_control_dock = QDockWidget('Magnet Control', self)
            self.magnet_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
            self.magnet_control_dock.setWidget(self.magnet_control)
        else:
            self.magnet_control_dock = None

        if self._check_vna:
            if self._vna_case == 'time':
                self.vna_source_control_dock = QDockWidget(f'VNA Control S_{self.gw.vna.S}(t)', self)
            if self._vna_case == 'frequency':
                self.vna_source_control_dock = QDockWidget(f'VNA Control S_{self.gw.vna.S}(f)', self)
            self.vna_source_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
            self.vna_source_control_dock.setWidget(self.vna_control)
        else:
            self.vna_source_control_dock = None

        if self._check_status:
            self.status_control_dock = QDockWidget('Status', self)
            self.status_control_dock.setMinimumWidth(MIN_DOCK_WIDTH)
            self.status_control_dock.setWidget(self.status_control)
        else:
            self.status_control_dock = None

        # add dock widgets
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree_dock)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.plot_form_dock)

        self.addDockWidget(Qt.RightDockWidgetArea, self.measurement_control_dock)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.jupyter_console_control_dock)

        if self._check_adwin:
            self.addDockWidget(Qt.RightDockWidgetArea, self.adwin_control_dock)
        if self._check_femtos:
            self.addDockWidget(Qt.RightDockWidgetArea, self.femto_control_dock)
        if self._check_source:
            self.addDockWidget(Qt.RightDockWidgetArea, self.source_control_dock)
        if self._check_motor:
            self.addDockWidget(Qt.RightDockWidgetArea, self.motor_control_dock)
        if self._check_magnet:
            self.addDockWidget(Qt.RightDockWidgetArea, self.magnet_control_dock)
        if self._check_vna:
            self.addDockWidget(Qt.RightDockWidgetArea, self.vna_source_control_dock)
        if self._check_status:
            self.addDockWidget(Qt.RightDockWidgetArea, self.status_control_dock)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.plot_form_dock)

        if self._check_status:
            self.splitDockWidget(self.measurement_control_dock, self.status_control_dock, Qt.Horizontal)
        if self._check_motor and self._check_magnet:
            self.splitDockWidget(self.magnet_control_dock, self.motor_control_dock, Qt.Horizontal)
        if self._check_adwin and self._check_femtos:
            self.splitDockWidget(self.adwin_control_dock, self.femto_control_dock, Qt.Horizontal)


        liste=[]
        liste.append(self.tree_dock.toggleViewAction())
        if self._check_adwin:
            liste.append(self.adwin_control_dock.toggleViewAction())
        if self._check_femtos:
            liste.append(self.femto_control_dock.toggleViewAction())
        if self._check_source:
            liste.append(self.source_control_dock.toggleViewAction())
        if self._check_motor:
            liste.append(self.motor_control_dock.toggleViewAction())
        if self._check_magnet:
            liste.append(self.magnet_control_dock.toggleViewAction())
        if self._check_vna:
            liste.append(self.vna_source_control_dock.toggleViewAction())
        if self._check_status:
            liste.append(self.status_control_dock.toggleViewAction())
        liste.append(self.plot_form_dock.toggleViewAction())
        liste.append(self.jupyter_console_control_dock.toggleViewAction())
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
        
class JupyterConsoleWidget(inprocess.QtInProcessRichJupyterWidget):
    def __init__(self):
        super().__init__()

        self.kernel_manager = inprocess.QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()
        
        kernel = self.kernel_manager.kernel
        kernel.shell.push(dict(np=np, InstrumentGateway=InstrumentGateway, DataGateway = DataGateway))

        self.execute("gw = InstrumentGateway()")
        self.execute("gw.connect()")

        self.execute("dgw = DataGateway()")
        self.execute("dgw.connect()")

        self.execute("clear")

    def shutdown_kernel(self):
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()


class JupyterMainWindow(QtWidgets.QMainWindow):
    def __init__(self, dark_mode=True):
        super().__init__()
        central_dock_area = DockArea()

        # create plot widget (and  dock)
        self.plot_widget = pg.PlotWidget()
        plot_dock = Dock(name="Plot Widget Dock", closable=True)
        plot_dock.addWidget(self.plot_widget)
        central_dock_area.addDock(plot_dock)

        # create jupyter console widget (and  dock)
        self.jupyter_console_widget = JupyterConsoleWidget()
        jupyter_console_dock = Dock("Jupyter Console Dock")
        jupyter_console_dock.addWidget(self.jupyter_console_widget)
        central_dock_area.addDock(jupyter_console_dock)
        self.setCentralWidget(central_dock_area)

        app = QtWidgets.QApplication.instance()
        app.aboutToQuit.connect(self.jupyter_console_widget.shutdown_kernel)

        kernel = self.jupyter_console_widget.kernel_manager.kernel
        kernel.shell.push(dict(np=np, pw=self.plot_widget))
#     main.jupyter_console_widget

        # set dark mode
        if dark_mode:
            # Set Dark bg color via this relatively roundabout method
            self.jupyter_console_widget.set_default_style(
                "linux"
            )

# if __name__ == "__main__":
#     pg.mkQApp()
#     main = MainWindow(dark_mode=True)
#     main.show()
#     main.jupyter_console_widget.execute('print("hello world :D ")')

#     # plot a sine/cosine waves by printing to console
#     # this is equivalent to typing the commands into the console manually
#     main.jupyter_console_widget.execute("x = np.arange(0, 3 * np.pi, .1)")
#     main.jupyter_console_widget.execute("pw.plotItem.plot(np.sin(x), pen='r')")
#     main.jupyter_console_widget.execute(
#         "pw.plotItem.plot(np.cos(x),\
#          pen='cyan',\
#          symbol='o',\
#          symbolPen='m',\
#          symbolBrush=(0,0,255))"
#     )
#     main.jupyter_console_widget.execute("whos")
#     main.jupyter_console_widget.execute("")

#     pg.exec()


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

