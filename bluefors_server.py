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

from p5control import InstrumentServer, drivers, inserv_cli
from core.drivers.calculator import Calculator
from core.drivers.faulhaber import Faulhaber
from core.drivers.thermometer import Keysight34461A_thermometer
from core.drivers.faulhaber import Faulhaber
from core.drivers.ground import Keysight34461A_ground
from core.drivers.femtos import FemtoDLPVA100B

# inserv = InstrumentServer(data_server_filename='.data//SUPERSHAPREFB.hdf5') #data_server_filename='.data/session0081.hdf5') #data_server_filename='.data/NoiseTest.hdf5')
inserv = InstrumentServer(data_server_filename='.data/session0108.hdf5')


inserv._add('adwin', drivers.ADwinGold2_v2)
# inserv._add('calc', Calculator)
# inserv._add('vna', drivers.ZNB40, '192.168.1.104')
inserv._add('motor', Faulhaber)
# inserv._add('multi_V1', drivers.Keysight34461A, 'TCPIP0::192.168.1.110::INSTR')
# inserv._add('multi_V2', drivers.Keysight34461A, 'TCPIP0::192.168.1.111::INSTR')
# inserv._add('ground', Keysight34461A_ground, 'TCPIP0::192.168.1.110::INSTR')
inserv._add('thermo', Keysight34461A_thermometer, 'TCPIP0::192.168.1.111::INSTR')
inserv._add('bluefors', drivers.BlueForsAPI)
inserv._add('femtos', FemtoDLPVA100B)


print("Added instruments successfully.")

inserv.start()

inserv_cli(inserv)

inserv._remove('femtos')


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