# setup logging
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='server_v2.log',
    level=logging.DEBUG,
    filemode='w', # overwrites logs every time this script is started
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(thread)6d %(name)-30s %(funcName)-20s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

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

"""
Initialize Instrument Server
"""
inserv = InstrumentServer()
# inserv = InstrumentServer(data_server_filename='R_ref^4K over T_still.hdf5')

"""
Add Devices
"""

inserv._add('adwin', ADwinGold2)
inserv._add('femto', Femto)
inserv._add('rref', Rref, R_ref = 100e3)

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

