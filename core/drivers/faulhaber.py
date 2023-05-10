import logging
import time
import os

import numpy as np
from ADwin import ADwin
from threading import Lock
from time import sleep
from pyvisa import ResourceManager

from core.utilities.config import dump_to_config, load_from_config

from p5control.drivers.basedriver import BaseDriver
from p5control import DataGateway, InstrumentGateway

logger = logging.getLogger(__name__)

class Faulhaber(BaseDriver):
    """
    Modell: Faulhaber MCDC 300-2 S
    Parameters
    ----------
    name : str
        name for this instance
    """

    def __init__(self, name: str):
        # super().__init__()
        
        self.refresh_delay = 0.5

        self._name = name
        self._address = 1

        self.lock = Lock()

        self._norm_turn = 1e8
        self._target_pos = np.NAN
        self._target_speed = 7000

        self._moving = False
        self._counter = 0
        self._idle_interval = 10

        self.open()
        self.initialize()
    
    def open(self):
        # Connect to pyvisa
        rm = ResourceManager()
        self._inst = rm.open_resource(f"ASRL{self._address}::INSTR")
        self._inst.read_termination = "\r\n"
        self._inst.timeout = 1000

        logger.info('opened resource "%s" at address "%s"', self._name, self._address)

    def close(self):
        #disconnect
        logger.info('closing resource "%s" at address "%s"', self._name, self._address)
        self._inst.close()
            
    def initialize(self):
        ok = self.query("EN")
        if ok:
            logger.info("%s Connection is established!", self._name)
        else:
            logger.error("%s Connection was not established.", self._name)

        glob_pos = self.load_global_position_from_config()
        self.query(f"HO{glob_pos}")

        upper_limit = self.get_global_upper_limit()
        self.query(f"LL{upper_limit}")

        lower_limit = self.get_global_lower_limit()
        self.query(f"LL{lower_limit}")

        self.query('NP')
        self.query(f"SP{self._target_speed}")

    def stop_measuring(self):
        # disable motor
        logger.info("%s Close connection.", self._name)
        self.query("DI")

    def query(self, string:str):
        with self.lock:
            reading = self._inst.query(string)

            # handles notifier
            match reading:
                case 'p':
                    self._moving = False
                    reading = self._inst.read()
                    # print('reached', self._inst.query('pos'))
                    self._inst.query('NP')

            # print(string, reading)
            # handles valid and invalid input
            match reading:
                case 'OK':
                    return True
                case 'Invalid parameter':
                    logger.warning('%s.query(): Encountered invalid parameter.')
                    return False
                case _:
                    return reading

    def retrieve_data(self):
        now = time.time()
        position = float(self.query("POS"))/self._norm_turn 
        speed = int(self.query('GN')) # actual turns / min
        current = float(self.query('GRC'))*1e-3 # A
        return {
            "time": now,
            "position": position,
            "speed": speed,
            "current": current,
            }

    def get_data(self):
        logger.debug('%s.get_data()', self._name)
        # get position
        # get speed / current
        if self._moving:
            return self.retrieve_data()
        else:
            if (self._counter * self.refresh_delay) > self._idle_interval:
                self._counter = 0
                return self.retrieve_data()
            else:
                self._counter += 1
                sleep(self.refresh_delay)

    def get_status(self):
        logger.debug('%s.get_status()', self._name)

        now = time.time()
        position = float(self.query("POS"))
        turns = position/self._norm_turn 
        # speed = int(self.query('GN')) # actual turns / min
        # current = float(self.query('GRC'))*1e-3 # A
        temperature = int(self.query('TEM')) # °C

        self.write_global_position_to_config(int(position))

        return {
            "time": now,
            "position": turns,
            # "speed": speed,
            # "current": current,
            "moving": self._moving,
            "temperature": temperature,
            }
    
    
    def set_moving(self, moving:bool):
        if moving:
            logger.debug('%s.set_moving(True)', self._name)
            self.query("M")
        else:
            logger.debug('%s.set_moving(False)', self._name)
            self.query("V0")
        self._moving = moving

    def get_moving(self):
        logger.debug('%s.get_moving()', self._name)
        return self._moving
    
    def stop_query(self, query:str):
        if self._moving:
            self.query("V0")
            has_been_moving = True
        else:
            has_been_moving = False
        self.query(query)
        if has_been_moving:
            self.query("NP")
            self.query("M")

    def set_target_position(self, turns:float):
        logger.debug('%s.set_target_position(%s)', self._name, turns)
        position = int(turns*self._norm_turn)
        self.stop_query(f"LA{position}")
        self._target_pos = turns

    def get_target_position(self):
        logger.debug('%s.get_target_position()', self._name)
        if self._moving:
            return self.query("TPOS")
        else:
            return self._target_pos
    
    def set_target_speed(self, speed:int):
        logger.debug('%s.set_target_speed(%s)', self._name, speed)
        self.stop_query(f"SP{speed}")
        self._target_speed = speed

    def get_target_speed(self):
        logger.debug('%s.get_target_speed()', self._name)
        if self._moving:
            return self.query("GV")
        else:
            return self._target_speed

    def write_global_position_to_config(self, position):
        motor_dict = load_from_config('motor')
        my_dict = {
            'motor': {
                'position': position,
                'upper_limit': motor_dict['upper_limit'],
                'lower_limit': motor_dict['lower_limit'],
                }
        }
        dump_to_config(my_dict)

    def load_global_position_from_config(self):
        return load_from_config('motor')['position']
    
    def get_global_upper_limit(self):
        return load_from_config('motor')['upper_limit']

    def get_global_lower_limit(self):
        return load_from_config('motor')['lower_limit']

    def set_idle_time(self, value:float):
        self._idle_interval = value

    def get_idle_time(self):
        return self._idle_interval