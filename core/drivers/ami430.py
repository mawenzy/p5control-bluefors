"""
Driver for AM430 Magnet
"""
import time
import logging

from pyvisa import ResourceManager
from threading import Lock

from p5control.drivers.basedriver import BaseDriver, BaseDriverError

import numpy as np

logger = logging.getLogger(__name__)

class AMI430(BaseDriver):
    """Driver for the AM430 or AMI430, specifically used in BlueFors @ P10. Since it is MessageBased, we can use much
    of the ThreadSafeBaseDriver class.
    """

    def open(self):
        """Open connection to the device.
        
        Overwritten to add the termination characters and reset the device after it has been
        connected.
        """


        self.lock = Lock()

        rm = ResourceManager()
        self._inst= rm.open_resource(f'TCPIP::{self._address}::7180::SOCKET')

        with self.lock:
            self._inst.write_termination = u'\r\n'
            self._inst.read_termination = u'\r\n'
            self._inst.timeout=2000
            self._inst.chunk_size = 20480 #100kb

            self._running = False

            _ = self._inst.read() # Instrument is stupid
            _ = self._inst.read() # Instrument is really stupid

        logger.info('opened resource "%s" at address "%s"', self._name, self._address)
        
        # BlueFors AMI430 Specifications
        self._seg_field_lower = 5.325
        self._seg_rate_lower = 0.2106
        self._seg_field_upper = 7
        self._seg_rate_upper = 0.1053       

        # Testing Specifications
        self._seg_field_lower = 0.5
        self._seg_rate_lower = 0.2
        self._seg_field_upper = 0.7
        self._seg_rate_upper = 0.1     

        self.reset()
        self.remote_control()
        self.setup_instrument()
        self.pause() 

    def reset(self):
        logger.debug('%s.reset()', self._name)
        with self.lock:
            self._inst.write('*RST')
            self._inst.write('*CLS') # clear event register, probably not usable
            self._inst.query('*OPC?')

    def remote_control(self):
        logger.debug('%s.remote_control()', self._name)
        with self.lock:
            self._inst.write('SYSTem:REMote')
            self._inst.query('*OPC?')

    def local_control(self):
        logger.debug('%s.local_control()', self._name)
        with self.lock:
            self._inst.write('SYSTem:LOCal')
            self._inst.query('*OPC?')

    def setup_instrument(self):
        logger.debug('%s.setup_instrument()', self._name)
        with self.lock:
            # Each 4th write should be interrupted with *OPC?
            # units tesla/min
            self._inst.write('CONFigure:FIELD:UNITS 1') #T
            self._inst.write('CONFigure:RAMP:RATE:UNITS 1') #1/min
            self._inst.query('*OPC?')
            # calibration factor
            self._inst.write('CONFigure:COILconst 0.106500')
            # max current
            self._inst.write('CONFigure:CURRent:LIMit 65')
            # quench detect on 1, 0 off
            self._inst.write('CONFigure:QUench:DETect 0')
            self._inst.query('*OPC?')
            # set segments (target ramp)
            self._inst.write('CONFigure:RAMP:RATE:SEGments 2')
            self._inst.write(f'CONFigure:RAMP:RATE:FIELD 1, {self._seg_rate_lower}, {self._seg_field_lower}')
            self._inst.write(f'CONFigure:RAMP:RATE:FIELD 2, {self._seg_rate_upper}, {self._seg_field_upper}')
            self._inst.query('*OPC?')
            self._rate = 0
            # set segments (external ramp down)
            self._inst.write('CONFigure:RAMPDown:RATE:SEGments 2')
            self._inst.write(f'CONFigure:RAMPDown:RATE:FIELD 1, {self._seg_rate_lower}, {self._seg_field_lower}')
            self._inst.write(f'CONFigure:RAMPDown:RATE:FIELD 2, {self._seg_rate_upper}, {self._seg_field_upper}')
            self._inst.query('*OPC?')     

        self._rate = 0.0
        self._target = 0.0
        self._field = 0.0

    def close(self):
        """Close connection to the device and reset self.._inst.variable to None
        
        Raises
        ------
        BaseDriverError
            if no connection exists which can be closed
        """
        if not self._inst:
            raise BaseDriverError(
                f'connection to device {self._name} cannot be closed since it is not open.'
            )

        logger.info('closing resource "%s" at address "%s"', self._name, self._address)
        # self.goto_zero()
        self.local_control()
        self._inst.close()
        self._inst= None

    def start_measuring(self):
        self._running = True
    
    def stop_measuring(self):
        self._running = False

    def get_status(self):
        logger.debug('%s.get_status()', self._name)
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
        logger.debug('%s.get_data()', self._name)
        return {
            "time": float(time.time()),
            "field": float(self.get_field()),
        }
        
    '''
    Attributes
    '''
    
    def get_field(self):
        logger.debug('%s.get_field()', self._name)
        with self.lock:
            field = float(self._inst.query('FIELD:MAGnet?'))  
        self._field = field
        return field
    
    def get_status_field(self):
        if not self._running:
            self.get_field()
        return self._field

    def ramp(self):
        logger.debug('%s.ramp()', self._name)
        with self.lock:
            self._inst.write('RAMP')
            self._inst.query('*OPC?')
        self._state = True

    def pause(self):
        logger.debug('%s.pause()', self._name)
        with self.lock:
            self._inst.write('PAUSE')
            self._inst.query('*OPC?')
        self._state = False
        
    def goto_zero(self):
        logger.debug('%s.goto_zero()', self._name)
        with self.lock:
            self._inst.write('ZERO')
            self._inst.query('*OPC?')

    def get_state(self):

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
        with self.lock:
            state = int(self._inst.query('STATE?'))
            logger.debug(state)
        return state

    # def get_state(self):
    #     logger.debug('%s.get_state()', self._name)
    #     if self._state:
    #         if np.abs(self._target - self._field) <= 1e-4:
    #             self._state = False
    #     return self._state

    def set_rate(self, rate: float):
        logger.debug('%s.set_rate()', self._name)
        self._rate = rate
        with self.lock:
            if 0 < rate <= self._seg_rate_upper:
                self._inst.write('CONFigure:RAMP:RATE:SEGments 1')
                self._inst.write(f'CONFigure:RAMP:RATE:FIELD 1,{rate:6.5f},{self._seg_field_upper}')
                self._inst.query('*OPC?') 
            elif self._seg_rate_upper < rate <= self._seg_rate_lower:
                self._inst.write('CONFigure:RAMP:RATE:SEGments 2')
                self._inst.write(f'CONFigure:RAMP:RATE:FIELD 1,{rate:6.5f},{self._seg_field_lower}')
                self._inst.write(f'CONFigure:RAMP:RATE:FIELD 2,{self._seg_rate_upper},{self._seg_field_upper}')
                self._inst.query('*OPC?')
            else:
                rate = 0
                self._inst.write('CONFigure:RAMP:RATE:SEGments 2')
                self._inst.write(f'CONFigure:RAMP:RATE:FIELD 1,{self._seg_rate_lower},{self._seg_field_lower}')
                self._inst.write(f'CONFigure:RAMP:RATE:FIELD 2,{self._seg_rate_upper},{self._seg_field_upper}')
                self._inst.query('*OPC?')

    def get_rate(self):
        logger.debug('%s.get_rate()', self._name)
        return float(self._rate)

    def set_target_field(self, target: float):
        logger.debug('%s.set_target_field(%f)', self._name, target)
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
        with self.lock:
            self._inst.write(f'CONFigure:FIELD:TARGet {target:6.5f}')
            self._target = float(self._inst.query(f'FIELD:TARGet?'))

    def get_target_field(self):
        logger.debug('%s.get_target_field()', self._name)
        target = self._target
        return float(target)
    
