import logging
import time
import pyvisa

import numpy as np

from p5control.drivers.basedriver import BaseDriver, ThreadSafeBaseDriver
from p5control import DataGateway, InstrumentGateway


logger = logging.getLogger(__name__)

class KeysightP5028A(ThreadSafeBaseDriver):
    def __init__(self, 
                 name,              
                 address='TCPIP0::DESKTOP-T9V68NA::hislip_PXI10_CHASSIS1_SLOT1_INDEX0::INSTR', 
                 case = 'time',
                 S = '11',
                 res: float = 0.1):
        
        self._name = name
        self._address = address
        self.refresh_delay = 1
        case = 'time'
        
        self.case = case
        self.S = S

        self.input_channel = int(S[0])
        self.output_channel = int(S[1])
        
        self.output = 0
        self.power = 0.0

        # t sweep       
        self.tsweep_frequency = 0.0
        self.tsweep_measuring = 0

        self.open()
        self.initialize()

    def open(self):
        logger.debug('%s.open()', self._name)
        rm = pyvisa.ResourceManager()
        self._inst = rm.open_resource(self._address)  
        self._inst.timeout=1e5 
        self._inst.read_termination = '\n'

    def query(self, request):
        output = self._inst.query(request)
        return output
    def write(self, writing):
        self._inst.write(writing)
    def read(self):
        output = self._inst.read()
        return output

    def initialize(self):
        self.write('*RST')
        self.write("SYST:FPR")
        self.write('CALC:PAR:DEL:ALL')
        self.write(f'OUTP:STAT OFF')
        self.write(f"CALC1:MEAS1:DEF 'R{self.output_channel},{self.output_channel}'")
        self.write(f"DISP:WIND1:STAT ON")
        self.write(f"DISP:MEAS1:FEED 1")
        self.write(f'SENS:SWE:TYPE CW')
        self.setup_measuring()

    def close(self):
        logger.debug('%s.close()', self._name)
        self.write('*RST')
        self.write(f'OUTP:STAT OFF')
        
    def setup_measuring(self):
        pass

    def get_data(self):
        return None    
    
    def _save_data(
        self,
        hdf5_path: str,
        data,
        dgw: DataGateway,
    ):
        pass
    
    """
    Status
    """
    def get_status(self):
        status = {
                "time": time.time(),
                "output": self.output,
                "power": self.power,
                "frequency": self.tsweep_frequency,
            }
        return status

    def setOutput(self, output):
        logger.debug('%s.setOutput()', self._name)
        if output:
            self.write(f'OUTP:STAT ON')
        else:
            self.write(f'OUTP:STAT OFF')
        self.output = output

    def getOutput(self):
        return self.output

    def setPower(self, value):
        logger.debug('%s.setPower()', self._name)
        self.write(f'SOUR:POW:LEV:IMM:AMPL {value}')
        self.power = value

    def setTSweepFrequency(self, frequency):
        logger.debug('%s.setTSweepFrequency()', self._name)
        self.write(f'SENS:FREQ:CW {frequency}')
        self.tsweep_frequency = frequency
    
    def getTSweepFrequency(self):
        return self.tsweep_frequency
    
    def getPower(self):
        return self.power
    
    def getPoints(self):
        return 0
    def getBandwidth(self):
        return 0