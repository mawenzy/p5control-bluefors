# setup logging
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='.logs/viewer.log',
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

        self.init_actions()
        self.init_menus()
        self.init_toolbars()
        self.init_statusbar()
        self.init_widgets()
        self.init_docks()
        self.init_signals()



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


        # add dock widgets
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree_dock)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.plot_form_dock)


        self.addDockWidget(Qt.LeftDockWidgetArea, self.plot_form_dock)


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

