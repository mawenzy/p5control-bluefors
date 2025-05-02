
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
        logger.info('%s.__init__()', name)
        self._name = 'Dummy '+name
        self.refresh_delay = refresh_delay

    """
    Status
    """
    def get_status(self):
        logger.info('%s.get_status()', self._name)
        return {}

    def get_data(self):
        logger.info('%s.get_data()', self._name)
        return
        
    def open(self):
        logger.info('%s.open()', self._name)

    def close(self):
        logger.info('%s.close()', self._name)

    def reset(self):
        logger.info('%s.reset()', self._name)

    def remote_control(self):
        logger.info('%s.remote_control()', self._name)

    def local_control(self):
        logger.info('%s.local_control()', self._name)

    def setup_instrument(self):
        logger.info('%s.setup_instrument()', self._name)

    def start_measuring(self):
        logger.info('%s.start_measuring()', self._name)
        
    def stop_measuring(self):
        logger.info('%s.stop_measuring()', self._name)
        
    def message(self, message:str="DON'T TOUCH\nRemote test running..."):
        logger.info('%s.message()', self._name)

    def initialize(self):
        logger.info('%s.initialize()', self._name)
        
    '''
    Attributes
    '''
    
    def get_field(self):
        logger.info('%s.get_field()', self._name)
        return np.nan
    
    def get_status_field(self):
        logger.info('%s.get_status_field()', self._name)
        return np.nan
        
    def ramp(self):
        logger.info('%s.ramp()', self._name)

    def pause(self):
        logger.info('%s.pause()', self._name)
        
    def goto_zero(self):
        logger.info('%s.goto_zero()', self._name)

    def get_state(self):
        logger.info('%s.get_state()', self._name)
        return 1

    def set_rate(self, rate: float):
        logger.info('%s.set_rate()', self._name)

    def get_rate(self):
        logger.info('%s.get_rate()', self._name)
        return np.nan

    def set_target_field(self, target: float):
        logger.info('%s.set_target_field(%f)', self._name, target)

    def get_target_field(self):
        logger.info('%s.get_target_field()', self._name)
        return np.nan

    def setFrequency(self, frequency):
        logger.info('%s.setFrequency()', self._name)

    def getFrequency(self):
        logger.info('%s.getFrequency()', self._name)
        return 0.0

    def setPower(self, value):
        logger.info('%s.setPower()', self._name)

    def getPower(self):
        logger.info('%s.getPower()', self._name)
        return -100.0   
    
    def setAmplitude(self, amplitude:float):
        logger.info('%s.setAmplitude()', self._name)
    
    def getAmplitude(self):
        logger.info('%s.getAmplitude()', self._name)
        return -1.0
    def reset_zero_pos(self):
        logger.info('%s.reset_zero_pos', self._name)
        self.query("HO")
    
    def set_moving(self, moving:bool):
        logger.info('%s.set_moving()', self._name)

    def get_moving(self):
        logger.info('%s.get_moving()', self._name)
        return 0

    def set_target_position(self, turns:float):
        logger.info('%s.set_target_position(%s)', self._name, turns)

    def get_target_position(self):
        logger.info('%s.get_target_position()', self._name)
        return 20
    
    def set_target_speed(self, speed:int):
        logger.info('%s.set_target_speed(%s)', self._name, speed)

    def get_target_speed(self):
        logger.info('%s.get_target_speed()', self._name)
        return -1
    
    
    def start_measurement(self):
        logger.info("%s.start_measurement()", self._name)

    def setVoltage(self, voltage):
        logger.info("%s.setVoltage()", self._name)
    def getVoltage(self):
        logger.info("%s.getVoltage()", self._name)
        return np.nan
    
    def setOutput(self, output):
        logger.info("%s.setOutput()", self._name)
    def getOutput(self):
        logger.info("%s.getOutput()", self._name)
        return 0
    
    def setRange(self, range):
        logger.info("%s.setRange()", self._name)
    def getRange(self):
        logger.info("%s.getRange()", self._name)
        return 1000

    def setAutoRange(self, voltage):
        logger.info("%s.setAutoRange()", self._name)
        autorange = np.copy(self.possible_ranges)
        autorange[autorange < np.abs(voltage)] = np.nan
        range = np.nanmin(autorange)
        self.setRange(range)

    def setCompliance(self, compliance):
        logger.info("%s.setCompliance()", self._name)
    def getCompliance(self):
        logger.info("%s.getCompliance()", self._name)
        return 0