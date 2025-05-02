
import logging

import numpy as np

from p5control.drivers.basedriver import BaseDriver

logger = logging.getLogger(__name__)

class Dummy(BaseDriver):
    """Dummy Driver for magnet, vna, yoko & Motor.
    """
    def __init__(
            self,
            name: str,
            refresh_delay: float = 0.5,
        ):
        logger.error('%s.__init__()', name)
        self._name = 'Dummy '+name
        self.refresh_delay = refresh_delay

    """
    Status
    """
    def get_status(self):
        logger.error('%s.get_status()', self._name)
        return {}

    def get_data(self):
        logger.error('%s.get_data()', self._name)
        return
        
    def open(self):
        logger.error('%s.open()', self._name)

    def close(self):
        logger.error('%s.close()', self._name)

    def reset(self):
        logger.error('%s.reset()', self._name)

    def remote_control(self):
        logger.error('%s.remote_control()', self._name)

    def local_control(self):
        logger.error('%s.local_control()', self._name)

    def setup_instrument(self):
        logger.error('%s.setup_instrument()', self._name)

    def start_measuring(self):
        logger.error('%s.start_measuring()', self._name)
        
    def stop_measuring(self):
        logger.error('%s.stop_measuring()', self._name)
        
    def message(self, message:str="DON'T TOUCH\nRemote test running..."):
        logger.error('%s.message()', self._name)

    def initialize(self):
        logger.error('%s.initialize()', self._name)
        
    '''
    Attributes
    '''
    
    def get_field(self):
        logger.error('%s.get_field()', self._name)
        return np.nan
    
    def get_status_field(self):
        logger.error('%s.get_status_field()', self._name)
        return np.nan
        
    def ramp(self):
        logger.error('%s.ramp()', self._name)

    def pause(self):
        logger.error('%s.pause()', self._name)
        
    def goto_zero(self):
        logger.error('%s.goto_zero()', self._name)

    def get_state(self):
        logger.error('%s.get_state()', self._name)
        return 1

    def set_rate(self, rate: float):
        logger.error('%s.set_rate()', self._name)

    def get_rate(self):
        logger.error('%s.get_rate()', self._name)
        return np.nan

    def set_target_field(self, target: float):
        logger.error('%s.set_target_field(%f)', self._name, target)

    def get_target_field(self):
        logger.error('%s.get_target_field()', self._name)
        return np.nan

    def setFrequency(self, frequency):
        logger.error('%s.setFrequency()', self._name)

    def getFrequency(self):
        logger.error('%s.getFrequency()', self._name)
        return 0.0

    def setPower(self, value):
        logger.error('%s.setPower()', self._name)

    def getPower(self):
        logger.error('%s.getPower()', self._name)
        return -100.0   
    
    def setAmplitude(self, amplitude:float):
        logger.error('%s.setAmplitude()', self._name)
    
    def getAmplitude(self):
        logger.error('%s.getAmplitude()', self._name)
        return -1.0
    def reset_zero_pos(self):
        logger.error('%s.reset_zero_pos', self._name)
        self.query("HO")
    
    def set_moving(self, moving:bool):
        logger.error('%s.set_moving()', self._name)

    def get_moving(self):
        logger.error('%s.get_moving()', self._name)
        return 0

    def set_target_position(self, turns:float):
        logger.error('%s.set_target_position(%s)', self._name, turns)

    def get_target_position(self):
        logger.error('%s.get_target_position()', self._name)
        return 20
    
    def set_target_speed(self, speed:int):
        logger.error('%s.set_target_speed(%s)', self._name, speed)

    def get_target_speed(self):
        logger.error('%s.get_target_speed()', self._name)
        return -1
    
    
    def start_measurement(self):
        logger.error("%s.start_measurement()", self._name)

    def setVoltage(self, voltage):
        logger.error("%s.setVoltage()", self._name)
    def getVoltage(self):
        logger.error("%s.getVoltage()", self._name)
        return np.nan
    
    def setOutput(self, output):
        logger.error("%s.setOutput()", self._name)
    def getOutput(self):
        logger.error("%s.getOutput()", self._name)
        return 0
    
    def setRange(self, range):
        logger.error("%s.setRange()", self._name)
    def getRange(self):
        logger.error("%s.getRange()", self._name)
        return 1000

    def setAutoRange(self, voltage):
        logger.error("%s.setAutoRange()", self._name)
        autorange = np.copy(self.possible_ranges)
        autorange[autorange < np.abs(voltage)] = np.nan
        range = np.nanmin(autorange)
        self.setRange(range)

    def setCompliance(self, compliance):
        logger.error("%s.setCompliance()", self._name)
    def getCompliance(self):
        logger.error("%s.getCompliance()", self._name)
        return 0