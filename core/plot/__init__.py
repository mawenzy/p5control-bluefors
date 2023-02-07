from .lnspc import LnSpcPlotConfig

# configure plot configs to work with p5control
from p5control.gui import setPlotConfigOption
setPlotConfigOption('lnspc', LnSpcPlotConfig)