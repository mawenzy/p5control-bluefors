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

class ADwinGold2(BaseDriver):
    def __init__(self, name: str):
        self._name = name
        self.version = 'v6'

        self.refresh_delay = .1

        self.open()
        self.lock = Lock()
        self._time_offset = time.time()

        sleep(.1)

        self.averaging = self.getAveraging()
        self.output = self.getOutput()

        self.sweeping = self.getSweeping()
        self.amplitude = self.getAmplitude()
        self.period = self.getPeriod()

        self.V1_off = np.nan
        self.V2_off = np.nan

        self.calculating = True
        self.current_threshold = 0

        self.V1_ovl = False
        self.V2_ovl = False

    def open(self):
        """Opens connection to ADwin."""
        self.inst = ADwin()
        self.inst.Boot(os.path.join(os.path.dirname(__file__), "external/ADwin11.btl"))
        self.inst.Load_Process(os.path.join(os.path.dirname(__file__), "external/adwingold2_v6.TB0"))
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

        V1_ovl = self.V1_ovl
        V2_ovl = self.V2_ovl
        self.V1_ovl = False
        self.V2_ovl = False

        return {
            "averaging": self.averaging,
            "output": self.output,
            "sweeping": self.sweeping,
            "amplitude": self.amplitude,
            "calculating": self.calculating,
            "period": self.period,
            "V1_off": self.V1_off,
            "V2_off": self.V2_off,
            "V1_ovl": V1_ovl,
            "V2_ovl": V2_ovl,
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

    def get_data(self):
        logger.debug('%s.get_data()', self._name)     
        with self.lock:
            l = [
                self.inst.Fifo_Full(FifoNo=1),
                self.inst.Fifo_Full(FifoNo=2),
                self.inst.Fifo_Full(FifoNo=8),
                self.inst.Fifo_Full(FifoNo=9),
                    ]

        l = list(map(int, l))
        count = min(l)
        if count <= 0:
            return None

        with self.lock:
            V1 = np.array(self.inst.GetFifo_Double(FifoNo=1, Count=count), dtype='float64')
            V2 = np.array(self.inst.GetFifo_Double(FifoNo=2, Count=count), dtype='float64')

            trigger = np.array(self.inst.GetFifo_Double(FifoNo=8, Count=count), dtype='int')
            times = np.array(self.inst.GetFifo_Double(FifoNo=9, Count=count), dtype='float64') + self._time_offset

        if np.any(V1>=9.5) or np.any(V1<=-9.5):
            self.V1_ovl = True

        if np.any(V2>=9.5) or np.any(V2<=-9.5):
            self.V2_ovl = True
            
        return {
            "time": list(times),
            "V1": list(V1),
            "V2": list(V2),
            "trigger": list(trigger),
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
            "trigger": array['trigger'],
        }
        dgw.append(
            adwin_path, 
            adwin_data, 
            max_length=int(1e5), 
            **kwargs
            )

        # Take care of saving V_off
        if not self.output or self.amplitude==0:
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
        if self.calculating and self.output:
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

            # Handle Calculations
            t = array["time"]
            V = (np.array(array['V1'], dtype='float64') - V1_off) / amp_V1
            I = (np.array(array['V2'], dtype='float64') - V2_off) / amp_V2 / R_ref

            R = np.zeros(len(V))
            logic = np.abs(I) > self.current_threshold
            R[logic] = V[logic] / I[logic]
            R[np.abs(I) <= self.current_threshold] = np.nan     

            G_0 = 7.748e-5 #Siemens oder 1/Ohm
            G = 1 / R / G_0 
            # dIdV = np.gradient(I,V) / G_0 

            resistance_data = {
                "time": list(t),
                "G (G_0)": list(G),
                # "dI/dV (G_0)": list(dIdV),
                "R (Ohm)": list(R),
                "V (V)": list(V),
                "I (A)": list(I),
            }
            dgw.append(
                resistance_path, 
                resistance_data, 
                max_length=int(1e5), 
                **kwargs
                )


    """
    Properties
    - start / stop output
    - start / stop sweep
    - start / stop lockin
    - start / stop calculating
    - output
    - sweeping
    - locking
    - calculating
    - averaging
    - ranges
    - amplitude
    - period
    - lockin_amplitude
    - lockin_frequency
    - current threshold
    """

    def start_output(self):
        self.setOutput(True)
            
    def stop_output(self):
        self.setOutput(False)
        
    def start_sweep(self):
        self.setSweeping(True)
            
    def stop_sweep(self):
        self.setSweeping(False)

    def startCalculating(self):
        self.setCalculating(True)

    def stopCalculating(self):
        self.setCalculating(False)
        
    def setOutput(self, value:bool):
        logger.debug('%s.setOutput(%i)', self._name, value)
        with self.lock:
            self.inst.Set_Par(Index=11, Value=int(value))
        self.output = self.getOutput()

    def getOutput(self):
        logger.debug('%s.getOutput()', self._name)
        with self.lock:
            return bool(self.inst.Get_Par(11))
        
    def setSweeping(self, value:bool):
        logger.debug('%s.setSweeping(%i)', self._name, value)
        with self.lock:
            self.inst.Set_Par(Index=10, Value=int(value))
        self.sweeping = self.getSweeping()

    def getSweeping(self):
        logger.debug('%s.getSweeping()', self._name)
        with self.lock:
            return bool(self.inst.Get_Par(10))

    def setCalculating(self, value:bool):
        logger.debug('%s.setCalculating(%i)', self._name, value)
        self.calculating = value

    def getCalculating(self):
        logger.debug('%s.getCalculating()', self._name)
        return self.calculating

    def setAveraging(self, value:int):
        logger.debug('%s.setAveraging(%i)', self._name, value)
        with self.lock:
            self.inst.Set_Par(Index=9, Value=value)
        self.averaging = self.getAveraging()

    def getAveraging(self):
        logger.debug('%s.getAveraging()', self._name)
        with self.lock:
            return int(self.inst.Get_Par(9))
            
    def setAmplitude(self, value:float):
        logger.debug('%s.setAmplitude(%i)', self._name, value)
        with self.lock:
            self.inst.Set_FPar(Index=14, Value=value)
        self.amplitude = self.getAmplitude()

    def getAmplitude(self):
        logger.debug('%s.getAmplitude()', self._name)
        with self.lock:
            return float(self.inst.Get_FPar(14))
        
    def setPeriod(self, value:float):
        logger.debug('%s.setPeriod(%i)', self._name, value)
        with self.lock:
            self.inst.Set_FPar(Index=13, Value=value)
        self.period = self.getPeriod()

    def getPeriod(self):
        logger.debug('%s.getPeriod()', self._name)
        with self.lock:
            return float(self.inst.Get_FPar(13))
        
    def setCurrentThreshold(self, value:float):
        logger.debug('%s.setCurrentThreshold()', self._name)
        self.current_threshold = value

    def getCurrentThreshold(self):
        logger.debug('%s.getCurrentThreshold()', self._name)
        return self.current_threshold
    