"""
Driver for AM430 Magnet

version v2:
- better go to zero
- self._address is default already
"""
import time
import logging

from pyvisa import ResourceManager
from threading import Lock

from p5control.drivers.basedriver import ThreadSafeBaseDriver, BaseDriverError

import numpy as np

logger = logging.getLogger(__name__)

class AMI430(ThreadSafeBaseDriver):
    """Driver for the AM430 or AMI430, specifically used in BlueFors @ P10. Since it is MessageBased, we can use much
    of the ThreadSafeBaseDriver class.
    """
    def __init__(
            self,
            name: str,
            address: str = '192.168.1.103',
            refresh_delay: float = 0.5,
        ):
        logger.info('%s.__init__()', name)
        self._name = name
        self._address = address
        self._inst = None
        self.refresh_delay = refresh_delay
        self.open()
        
    def open(self):
        logger.info('%s.open()', self._name)
        self.lock = Lock()
        rm = ResourceManager()
        self._inst= rm.open_resource(f'TCPIP::{self._address}::7180::SOCKET')

        self._inst.write_termination = u'\r\n'
        self._inst.read_termination = u'\r\n'
        self._inst.timeout = 2000
        self._inst.chunk_size = 20480 #100kb

        _ = self.read() # Instrument is stupid
        _ = self.read() # Instrument is really stupid

        logger.info('opened resource "%s" at address "%s"', self._name, self._address)
        
        self._running = False

        # BlueFors AMI430 Specifications
        self._seg_field_lower = 5.325
        self._seg_rate_lower = 0.2106
        self._seg_field_upper = 7
        self._seg_rate_upper = 0.1053       

        # Testing Specifications
        # self._seg_field_lower = 0.05
        # self._seg_field_upper = 0.07   

        self.reset()
        self.remote_control()
        self.setup_instrument()

        self.set_rate(0.0)
        self.set_target_field(0.0)
        self._field = self.get_field()

    def reset(self):
        logger.info('%s.reset()', self._name)
        self.write('*RST')
        self.write('*CLS') # clear event register, probably not usable
        self.query('*OPC?')

    def remote_control(self):
        logger.info('%s.remote_control()', self._name)
        self.write('SYSTem:REMote')
        self.write('CONFigure:LOCK:ZEROfield 0')
        self.query('*OPC?')

    def local_control(self):
        logger.info('%s.local_control()', self._name)
        self.write('SYSTem:LOCal')
        self.query('*OPC?')

    def setup_instrument(self):
        logger.info('%s.setup_instrument()', self._name)
        # Each 4th write should be interrupted with *OPC?
        # units tesla/min
        self.write('CONFigure:FIELD:UNITS 1') #T
        self.write('CONFigure:RAMP:RATE:UNITS 1') #1/min
        self.query('*OPC?')
        # calibration factor
        self.write('CONFigure:COILconst 0.106500')
        # max current
        self.write('CONFigure:CURRent:LIMit 65')
        # quench detect on 1, 0 off
        self.write('CONFigure:QUench:DETect 0')
        self.query('*OPC?')
        # set segments (target ramp)
        self.write('CONFigure:RAMP:RATE:SEGments 2')
        self.write(f'CONFigure:RAMP:RATE:FIELD 1, {self._seg_rate_lower}, {self._seg_field_lower}')
        self.write(f'CONFigure:RAMP:RATE:FIELD 2, {self._seg_rate_upper}, {self._seg_field_upper}')
        self.query('*OPC?')
        # set segments (external ramp down)
        self.write('CONFigure:RAMPDown:RATE:SEGments 2')
        self.write(f'CONFigure:RAMPDown:RATE:FIELD 1, {self._seg_rate_lower}, {self._seg_field_lower}')
        self.write(f'CONFigure:RAMPDown:RATE:FIELD 2, {self._seg_rate_upper}, {self._seg_field_upper}')
        self.query('*OPC?')    

    def close(self):
        logger.info('%s.close()', self._name)
        self.local_control()
        logger.info('closing resource "%s" at address "%s"', self._name, self._address)

    def start_measuring(self):
        logger.info('%s.start_measuring()', self._name)
        self._running = True
    
    def stop_measuring(self):
        logger.info('%s.stop_measuring()', self._name)
        self._running = False

    def get_status(self):
        logger.info('%s.get_status()', self._name)
        now = time.time()
        field = self.get_status_field()
        state = self.get_state()
        rate = self.get_rate()
        target = self.get_target_field()
        status = {
            "time": now,
            "field": field,
            "state": state,
            "rate": rate,
            "target": target,
        }
        logger.debug('%s.get_status(): %s', self._name, str(status))
        return status

    def get_data(self):
        logger.info('%s.get_data()', self._name)
        return {
            "time": float(time.time()),
            "field": float(self.get_field()),
        }
        
    '''
    Attributes
    '''
    
    def get_field(self):
        logger.info('%s.get_field()', self._name)
        field = float(self.query('FIELD:MAGnet?'))  
        self._field = field
        return field
    
    def get_status_field(self):
        logger.info('%s.get_status_field()', self._name)
        if not self._running:
            _ = self.get_field()
        return self._field
        
    def ramp(self):
        logger.info('%s.ramp()', self._name)
        self.write('RAMP')
        self.query('*OPC?')
        self._state = True

    def pause(self):
        logger.info('%s.pause()', self._name)
        self.write('PAUSE')
        self.query('*OPC?')
        self._state = False
        
    def goto_zero(self):
        logger.info('%s.goto_zero()', self._name)
        self.write('ZERO')
        self.query('*OPC?')
        logger.info('%s.goto_zero()', self._name)

    def get_state(self):
        logger.info('%s.get_state()', self._name)

        #  1 RAMPING to target field/current
        #  2 HOLDING at the target field/current
        #  3 PAUSED
        #  4 Ramping in MANUAL UP mode
        #  5 Ramping in MANUAL DOWN mode
        #  6 ZEROING CURRENT (in progress)
        #  7 Quench detected
        #  8 At ZERO current
        #  9 Heating persistent switch
        # 10 Cooling persistent switch
        # 11 External Rampdown active

        logger.debug('%s.get_state()', self._name)
        state = int(self.query('STATE?'))
        logger.debug(state)
        return state

    def set_rate(self, rate: float):
        logger.info('%s.set_rate()', self._name)
        if 0 < rate <= self._seg_rate_upper:
            self.write('CONFigure:RAMP:RATE:SEGments 1')
            self.write(f'CONFigure:RAMP:RATE:FIELD 1,{rate:6.5f},{self._seg_field_upper}')
            self.query('*OPC?') 
        elif self._seg_rate_upper < rate <= self._seg_rate_lower:
            self.write('CONFigure:RAMP:RATE:SEGments 2')
            self.write(f'CONFigure:RAMP:RATE:FIELD 1,{rate:6.5f},{self._seg_field_lower}')
            self.write(f'CONFigure:RAMP:RATE:FIELD 2,{self._seg_rate_upper},{self._seg_field_upper}')
            self.query('*OPC?')
        else:
            rate = 0.0
            self.write('CONFigure:RAMP:RATE:SEGments 2')
            self.write(f'CONFigure:RAMP:RATE:FIELD 1,{self._seg_rate_lower},{self._seg_field_lower}')
            self.write(f'CONFigure:RAMP:RATE:FIELD 2,{self._seg_rate_upper},{self._seg_field_upper}')
            self.query('*OPC?')
        self._rate = rate

    def get_rate(self):
        logger.info('%s.get_rate()', self._name)
        return float(self._rate)

    def set_target_field(self, target: float):
        logger.info('%s.set_target_field(%f)', self._name, target)
        self._target = target
        rate = self.get_rate()
        if self._seg_rate_upper < rate <= self._seg_rate_lower: # get critical interval
            if target > self._seg_field_lower:
                target = self._seg_field_lower
            if target < -self._seg_field_lower:
                target = -self._seg_field_lower
        else: # each other case, assuming 0 <= rate <= 0.1053
            if target > self._seg_field_upper:
                target = self._seg_field_upper
            if target < -self._seg_field_upper:
                target = -self._seg_field_upper
        self.write(f'CONFigure:FIELD:TARGet {target:6.5f}')
        self._target = float(self.query(f'FIELD:TARGet?'))

    def get_target_field(self):
        logger.info('%s.get_target_field()', self._name)
        target = self._target
        return float(target)