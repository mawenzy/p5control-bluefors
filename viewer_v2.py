# setup logging
import logging
from time import time
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=f'.data/viewer_v2.log',
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

from qtpy.QtCore import (Qt, QTimer, Slot)

from qtpy.QtWidgets import (
    QMainWindow, 
    QApplication, 
    QDockWidget,
    QAction, 
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
        
        self.init_menus()
        self.init_toolbars()
        self.init_statusbar()
        self.init_widgets()
        self.init_docks()
        self.init_signals()


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

        liste=[]
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tree_dock)
        liste.append(self.tree_dock.toggleViewAction())

        self.addDockWidget(Qt.LeftDockWidgetArea, self.plot_form_dock)
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
        app.setApplicationName('Viewer v2')

        window = BlueForsGUIMainWindow(app, dgw, gw)
        window.show()

        timer = QTimer()
        timer.timeout.connect(window.update)
        timer.start(30)

        sys.exit(app.exec())

