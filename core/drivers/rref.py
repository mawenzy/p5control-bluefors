"""
Test driver to illustrate the inner workings of *p5control*.
"""
import logging
import time

import numpy as np

logger = logging.getLogger(__name__)

from p5control.drivers.basedriver import BaseDriver
from p5control import DataGateway, InstrumentGateway

STATUS_NAME = 'status'
BF_NAME = 'bluefors'
T_NAME = 'temperature'
STILL_NAME = 'Still'

class Rref(BaseDriver):
    """Represents an instrument which magically measures a sine wave. Both the frequency and the amplitude can be changed.

    Parameters
    ----------
    name : str
        name for this instance
    """

    def __init__(self, name: str, R_ref = None):
        self._name = name

        if R_ref is None:
            self.calculating = True
            self.R_ref = 1
        else:
            self.calculating = False
            self.R_ref = R_ref


    def open(self):
        pass

    def close(self):
        pass

    def start_measuring(self):
        pass

    def get_status(self):
        """Returns the current amplitude and frequency."""
        logger.debug("%s.get_status()", self._name)
        return {
            "time": time.time(),
            "R_ref": self.R_ref,
        }

    def get_data(self):
        return {}
    
    def set_rref(self, rref):
        logger.debug("%s.set_rref()", self._name)
        self.R_ref = rref

    def get_rref(self):
        logger.debug("%s.get_rref()", self._name)
        return self.R_ref
        
    
    # def _save_data(
    #     self,
    #     hdf5_path: str,
    #     array,
    #     dgw: DataGateway,
    #     **kwargs
    # ):
    #     if self.calculating:
    #         try:
    #             still_path = f"{STATUS_NAME}/{BF_NAME}/{T_NAME}/{STILL_NAME}"
    #             T = dgw.get_data(still_path, field='T', indices = slice(-2, -1, 1))[0]
    #             self.R_ref = 53000
    #         except KeyError:
    #             print('T not found.')
