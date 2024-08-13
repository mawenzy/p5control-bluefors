"""
Test driver to illustrate the inner workings of *p5control*.
"""
from time import time
from pyvisa import ResourceManager
from threading import Lock
import numpy as np

import logging
logger = logging.getLogger(__name__)

from p5control.drivers.basedriver import ThreadSafeBaseDriver # type:ignore

class YokogawaGS200(ThreadSafeBaseDriver):

    def __init__(
            self,
            name: str,
            ):
        logger.info('%s.__init__()', name)
        self._name = name
        self._address = 13

        # status stuff
        self.output = False
        self.voltage = 0
        self.range = 30
        self.nplc = 1
        self.compliance = .001

        self.possible_ranges = np.array([30, 10, 1, .1, .01])

        self.open()
        self.initialize()
        self.setOutput(self.output)
        self.setVoltage(self.voltage)
        self.setCompliance(self.compliance)



    def open(self):
        logger.info('%s.open()', self._name)
        self.lock = Lock()
        rm = ResourceManager()
        self._inst = rm.open_resource(f'GPIB0::{self._address}::INSTR')
        self._inst.read_termination = '\n' # type:ignore
        self._inst.timeout=1e4 # 10s

    def close(self):
        self.setOutput(False)

    def initialize(self):
        logger.info('%s.setup()', self._name)
        self.write(f'*RST')
        self.write(f':source:function voltage')
        self.write(f':sense:state 1')
        self.write(f':sense:nplc {self.nplc}')
        self.write(f':sense:delay 0')
        self.write(f':sense:trigger IMM')
        self.query(f'*OPC?')

    def get_status(self):
        logger.info("%s.get_status()", self._name)
        return {
            'output': self.output,
            'voltage': self.voltage,
            'range': self.range,
            'nplc': self.nplc,
            'compliance': self.compliance,
        }

    def get_data(self):
        logger.info("%s.get_data()", self._name)
        current = np.nan
        if self.output:
            current = float(self.query(':fetch?'))
        return {
            "time": time(),
            "current": current,
            }
    
    def start_measurement(self):
        logger.info("%s.start_measurement()", self._name)
        self.write(':sense:zero:execute')
        self.query('*OPC?')

    def setVoltage(self, voltage):
        logger.info("%s.setVoltage()", self._name)
        self.setAutoRange(voltage)
        self.write(f':source:level:fix {voltage:+2.7f}')
        self.query('*OPC?')
        self.voltage = voltage
    def getVoltage(self):
        logger.info("%s.getVoltage()", self._name)
        return self.voltage
    
    def setOutput(self, output):
        logger.info("%s.setOutput()", self._name)
        self.write(f':output {int(output)}')
        self.query('*OPC?')
        self.output = output
    def getOutput(self):
        logger.info("%s.getOutput()", self._name)
        return self.output
    
    def setRange(self, range):
        logger.info("%s.setRange()", self._name)
        self.write(f':source:range {range}')
        self.query('*OPC?')
        self.range = range
    def getRange(self):
        logger.info("%s.getRange()", self._name)
        return self.range

    def setAutoRange(self, voltage):
        logger.info("%s.setAutoRange()", self._name)
        autorange = np.copy(self.possible_ranges)
        autorange[autorange < np.abs(voltage)] = np.nan
        range = np.nanmin(autorange)
        self.setRange(range)

    def setCompliance(self, compliance):
        logger.info("%s.setCompliance()", self._name)
        self.write(f':source:protection:current {compliance}')
        self.query('*OPC?')
        self.compliance = compliance
    def getCompliance(self):
        logger.info("%s.getCompliance()", self._name)
        return self.compliance