'''
TODO for v2
- Motor
    - redesign what?
    - war eigentlich problemfrei..
- Magnet
    - test driver
    - check for command consistency
- Yoko
    - establish connection
    - simple gate
- Zürich
    - check for noice floor
    - check for voltage adder
- VNA
    - optional implement: measure power over time
    - very optional: fsweep
- Rref Callibration

GUI_v2 TODO:
test:
- MagnetGUI
- MotorGUI

de-dummify:
- GateGUI
- LockinGui

optional:
- vna_time
- vna_frequency

Callbacks von nicht aktiven widgets verstopfen eventuell GUI

'''

'''
Logger
'''
import logging
from time import time
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=f'.data/server_v2.log',
    level=logging.DEBUG,
    filemode='w', # overwrites logs every time this script is started
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(thread)6d %(name)-30s %(funcName)-20s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
'''
General Stuff
'''
import sys
sys.path.append('C:\\Users\\BlueFors\\Documents\\p5control\\p5control')
sys.path.append('C:\\Users\\BlueFors\\Documents\\p5control')
sys.path.append('C:\\Users\\BlueFors\\Documents')

from p5control import InstrumentServer, inserv_cli
from p5control.server.inserv import InstrumentServerError

"""
Device drivers
"""

from core.drivers_v2.adwingold2_v6 import ADwinGold2
from core.drivers_v2.femto_v2 import Femto
from core.drivers_v2.rref import Rref

from core.drivers_v2.blueforsapi_v2 import BlueForsAPI
from core.drivers_v2.ami430_v2 import AMI430

from core.drivers_v2.vna_v2 import ZNB40_source
from core.drivers_v2.yoko_v2 import YokogawaGS200

from core import Faulhaber

"""
Initialize Instrument Server
"""
inserv = InstrumentServer()
# inserv = InstrumentServer(data_server_filename='24-08-07_OI-24d-10_bias_over_gate_0.hdf5')

"""
Add Devices
"""

inserv._add('adwin', ADwinGold2, series_resistance=0)
inserv._add('rref',  Rref, R_ref = 5.2e4) # 100kOhm
inserv._add('femto', Femto)

inserv._add('vna',   ZNB40_source, S = '11')
inserv._add('gate',  YokogawaGS200)

inserv._add('bluefors', BlueForsAPI) # try to remove errors of sampleheater
# lockin

inserv._add('magnet', AMI430) # untested
inserv._add('motor',  Faulhaber)
 


"""
Start Instrument Server
"""
print("Added instruments successfully.")

inserv.start()

inserv_cli(inserv)

"""
Close Instrument Server
"""
try:
    inserv._remove('femto')
except InstrumentServerError or KeyError:
    pass

try:
    inserv._remove('vna')
except InstrumentServerError or KeyError:
    pass

try:
    inserv._remove('gate')
except InstrumentServerError or KeyError:
    pass

try:
    inserv._remove('magnet')
except InstrumentServerError or KeyError:
    pass

try:
    inserv._remove('bluefors')
except InstrumentServerError or KeyError:
    pass