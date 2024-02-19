# setup logging
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='bluefors_server.log',
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
from core import ADwinGold2, ADwinGold2_v2, ADwinGold2_v3, ADwinGold2_v4, ADwinGold2_v5_2ch
from core import FemtoDLPVA100B, FemtoDLPVA100B_BA
from core import Keysight34461A, Keysight34461A_fourwire, Keysight34461A_ground, Keysight34461A_ground_R, Keysight34461A_thermometer
from core import Calculator, Calculator2
from core import AMI430, BlueForsAPI, Faulhaber, GIR2002, KeysightB2962A, KeysightB2962A_v2, ZNB40, Rref
from core.drivers.keysightP5028A import KeysightP5028A # Keysight VNA

"""
Initialize Instrument Server
"""
inserv = InstrumentServer()
# inserv = InstrumentServer(data_server_filename='R_ref^4K over T_still.hdf5')


"""
Add Devices
"""

inserv._add('adwin', ADwinGold2_v4)
inserv._add('femtos', FemtoDLPVA100B)
inserv._add('R_ref', Rref, R_ref = 100000)
# inserv._add('adwin', ADwinGold2_v5_2ch)
# inserv._add('source', KeysightB2962A_v2, 'TCPIP0::192.168.1.113::INSTR')

inserv._add('bluefors', BlueForsAPI)
inserv._add('motor', Faulhaber)
# inserv._add('magnet', AMI430, '192.168.1.103')
# inserv._add('thermo', Keysight34461A_thermometer, 'TCPIP0::192.168.1.111::INSTR')
inserv._add('vna', ZNB40, '192.168.1.104', case = 'time', S = '11') # antenna=11, stripline=22

# Keysight reserve
# inserv._add('multi_V1', Keysight34461A, 'TCPIP0::192.168.1.110::INSTR')
# inserv._add('multi_V2', Keysight34461A, 'TCPIP0::192.168.1.111::INSTR')
# inserv._add('ground', Keysight34461A, 'TCPIP0::192.168.1.110::INSTR')
# inserv._add('ground', Keysight34461A_ground, 'TCPIP0::192.168.1.110::INSTR')
# inserv._add('ground', Keysight34461A_ground_R, 'TCPIP0::192.168.1.110::INSTR')
# inserv._add('fourwire', Keysight34461A_fourwire, 'TCPIP0::192.168.1.110::INSTR')




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
    inserv._remove('femtos')
except InstrumentServerError or KeyError:
    pass

try:
    inserv._remove('motor')
except InstrumentServerError or KeyError:
    pass

try:
    inserv._remove('magnet')
except InstrumentServerError or KeyError:
    pass

try:
    inserv._remove('vna')
except InstrumentServerError or KeyError:
    pass

"""
Archieve
"""
# inserv._add('inst1', drivers.ExampleInst)
# inserv._add('inst2', drivers.ExampleInst)
# inserv._add('bf', drivers.BlueForsAPI, address='134.34.143.28:49098')
# inserv._add('thermo', drivers.GIR2002, 'ASRL1::INSTR')
# inserv._add('multi_sourcer', drivers.Keysight34461A, 'TCPIP0::192.168.1.108::INSTR')
# inserv._add('multi_source', drivers.Keysight34461A, 'TCPIP0::192.168.1.109::INSTR')
# inserv._add('multi_sample', drivers.Keysight34461A, 'TCPIP0::192.168.1.110::INSTR')
# inserv._add('multi_reference', drivers.Keysight34461A, 'TCPIP0::192.168.1.111::INSTR')
# inserv._add("source_gate", drivers.KeysightB2962A, "TCPIP0::192.168.1.112::INSTR")
# inserv._add("source_bias", drivers.KeysightB2962A, "TCPIP0::192.168.1.113::INSTR")
# inserv._add('femtos')
# inserv._add('motor')
# inserv._add('magnet')