import logging
import time
import os

import numpy as np
from ADwin import ADwin
from threading import Lock
from time import sleep

from p5control.drivers.basedriver import BaseDriver
from p5control import DataGateway, InstrumentGateway

logger = logging.getLogger(__name__)

ADWIN_NAME = 'adwin'

STATUS_NAME = 'status'
OFFSET_NAME = 'offset'
RESISTANCE_NAME = 'resistance'

FEMTO_NAME = 'femtos'
RREF_NAME = 'R_ref'
SOURCE_NAME = 'source'

class ADwinGold2_v5_2ch(BaseDriver):
    def __init__(self, name: str):
        self._name = name
        self.version = 'v5_2ch'

        self.open()
        self.lock = Lock()
        self._time_offset = time.time()

        sleep(.1)

        self.averaging = self.getAveraging()
        self.patterns = np.arange(4)
        self.ranges = np.array([10, 10])
        self.psbl_ranges = 20/2**self.patterns
        
        self.V1_off = np.nan
        self.V2_off = np.nan

        self.calculating = False
        self.offseting = False
        self.current_threshold = 0

    def open(self):
        """Opens connection to ADwin."""
        self.inst = ADwin()
        self.inst.Boot(os.path.join(os.path.dirname(__file__), "adwin/ADwin11.btl"))
        self.inst.Load_Process(os.path.join(os.path.dirname(__file__), "adwin/adwingold2_v5_2ch.TB0"))
        self.inst.Start_Process(ProcessNo=10)
        status = self.inst.Process_Status(ProcessNo=10)
        logger.debug("%s.open(), status: %s", self._name, status)

    def close(self):
        """Just logs the call to debug."""
        logger.debug(f'{self._name}.close()')

    """
    Status measurement
    """
    def get_status(self):
        """Returns the current averaging and ranges."""
        logger.debug('%s.get_status()', self._name)
        return {
            "averaging": self.averaging,
            "range_ch1": self.ranges[0],
            "range_ch2": self.ranges[1],
            "V1_off": self.V1_off,
            "V2_off": self.V2_off,
        }

    """
    Measurement
    """
    def start_measuring(self):
        """Start the measurement. Clear FIFOs
        """
        logger.debug('%s.start_measuring()', self._name)
        self._time_offset = time.time()
        with self.lock:
            self.inst.Set_Par(Index=8, Value=1)
        # set back initials
        self.case = -2
        self.before = 0

    def get_data(self):
        logger.debug('%s.get_data()', self._name)     
        with self.lock:
            l = [
                self.inst.Fifo_Full(FifoNo=1),
                self.inst.Fifo_Full(FifoNo=2),
                self.inst.Fifo_Full(FifoNo=9),
                    ]

        l = list(map(int, l))
        count = min(l)
        if count <= 0:
            return None

        with self.lock:
            V1 = self.inst.GetFifo_Double(FifoNo=1, Count=count)
            V2 = self.inst.GetFifo_Double(FifoNo=2, Count=count)
            times = np.array(self.inst.GetFifo_Double(FifoNo=9, Count=count), dtype='float64') + self._time_offset
            
        return {
            "time": list(times),
            "V1": list(V1),
            "V2": list(V2),
        }
    
    """
    Saving
    """
    def _save_data(
        self,
        hdf5_path: str,
        array,
        dgw: DataGateway,
        **kwargs
    ):
        # Take care of empty array
        if array is None:
            return
        
        # Take care of normal saving
        adwin_path = f"{hdf5_path}/{ADWIN_NAME}"
        adwin_data = {
            "time": array['time'],
            "V1": array['V1'],
            "V2": array['V2'],
        }
        dgw.append(
            adwin_path, 
            adwin_data, 
            max_length=int(1e5), 
            **kwargs
            )
        
        # Take care of saving V_off

        try:
            source_path = f"{STATUS_NAME}/{SOURCE_NAME}"
            source = dgw.get_data(source_path, indices = slice(-2, -1, 1))
            source_output = source['output']
        except KeyError:
            logger.warning("%s._save_data() no source found!")
            source_output = True


        if self.offseting:
            offset_path = f"{hdf5_path}/{OFFSET_NAME}"
            self.V1_off = np.mean(array['V1'])
            self.V2_off = np.mean(array['V2'])

            offset_data = {
                "time": np.mean(array['time']),
                "V1_off": self.V1_off,
                "V2_off": self.V2_off,
            }

            dgw.append(
                offset_path, 
                offset_data, 
                max_length=int(1e5), 
                **kwargs
                )
            
        # Take care of saving R, V, I
        if self.calculating:
            resistance_path = f"{hdf5_path}/{RESISTANCE_NAME}"

            # Handle offset
            try:
                offset_path = f"{hdf5_path}/{OFFSET_NAME}"
                offset = dgw.get_data(offset_path, indices = slice(-2,-1,1))
                V1_off = offset['V1_off']
                V2_off = offset['V2_off']
            except KeyError:
                logger.warning("%s._save_data() no V_off found!")
                V1_off = 0
                V2_off = 0

            # Handle amplification
            try:
                femto_path = f"{STATUS_NAME}/{FEMTO_NAME}"
                femto = dgw.get_data(femto_path, indices = slice(-2, -1, 1))
                amp_V1 = femto['amp_A']
                amp_V2 = femto['amp_B']
            except KeyError:
                logger.warning("%s._save_data() no amp_V found!")
                amp_V1 = 1
                amp_V2 = 1

            # Handle R_ref
            try:
                rref_path = f"{STATUS_NAME}/{RREF_NAME}"
                rref = dgw.get_data(rref_path, indices = slice(-2, -1, 1))
                R_ref = rref['R_ref']
            except KeyError:
                logger.warning("%s._save_data() no R_ref found!")
                R_ref = 1

            try:
                # Handle Calculations
                t = array["time"]
                V = (np.array(array['V1'], dtype='float64') - V1_off) / amp_V1
                I = (np.array(array['V2'], dtype='float64') - V2_off) / amp_V2 / R_ref

                R = np.zeros(len(V))
                logic = np.abs(I) > self.current_threshold
                R[logic] = V[logic] / I[logic]
                R[np.abs(I) <= self.current_threshold] = np.nan     

                G = 1/R / 7.748091729e-5 

                resistance_data = {
                    "time": list(t),
                    "R": list(R),
                    "V": list(V),
                    "I": list(I),
                    "G/G_0": list(G),
                }
                dgw.append(
                    resistance_path, 
                    resistance_data, 
                    max_length=int(1e5), 
                    **kwargs
                    )
            except ValueError:
                # ValueError: operands could not be broadcast together with shapes (1686,) (0,)
                pass


    """
    Properties
    - set / get calculating
    - set / get offseting
    - set / get averaging
    - set / get ranges
    """

    def setCalculating(self, value:bool):
        logger.debug('%s.setCalculating(%i)', self._name, value)
        self.calculating = value

    def getCalculating(self):
        logger.debug('%s.getCalculating()', self._name)
        return self.calculating

    def setOffseting(self, value:bool):
        logger.debug('%s.setOffseting(%i)', self._name, value)
        self.offseting = value

    def getOffseting(self):
        logger.debug('%s.getOffseting()', self._name)
        return self.offseting

    def setAveraging(self, value:int):
        logger.debug('%s.setAveraging(%i)', self._name, value)
        with self.lock:
            self.inst.Set_Par(Index=9, Value=value)
        self.averaging = self.getAveraging()

    def getAveraging(self):
        logger.debug('%s.getAveraging()', self._name)
        with self.lock:
            return int(self.inst.Get_Par(9))

    def setRange(self, range, ch:int):
        logger.debug('%s.setRange(%f, %i)', self._name, range, ch)        
        index = np.argmin(np.abs(self.psbl_ranges-range*2))
        with self.lock:
            self.inst.Set_FPar(Index=ch, Value = self.psbl_ranges[index])
            self.inst.Set_Par(Index=ch, Value = int(self.patterns[index]))
        self.ranges[ch-1] = self.psbl_ranges[index]/2

    def getRange(self, ch:int):
        logger.debug('%s.getRange(%i)', self._name, ch)
        with self.lock:
            return self.inst.Get_FPar(ch)/2

    def setCurrentThreshold(self, value:float):
        logger.debug('%s.setCurrentThreshold()', self._name)
        self.current_threshold = value

    def getCurrentThreshold(self):
        logger.debug('%s.getCurrentThreshold()', self._name)
        return self.current_threshold
            