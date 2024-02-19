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
LOCKIN_NAME = 'lockin'

STATUS_NAME = 'status/'
CALC_NAME = 'calc/'
OFFSET_NAME = 'offset'
STARTSTOP_NAME = 'startstop'
RESISTANCE_NAME = 'resistance'

SENSOR_NAME = 'sensor'
SWEEP_NAME = 'sweep'
LOCKIN_NAME = 'lockin'
OUTPUT_NAME = 'output'

class ADwinGold2_v4(BaseDriver):
    def __init__(self, name: str):
        self._name = name

        self.open()
        self.lock = Lock()
        self._time_offset = time.time()

        sleep(.1)

        self.averaging = self.getAveraging()
        self.patterns = np.arange(4)
        self.ranges = np.array([10, 10])
        self.psbl_ranges = 20/2**self.patterns

        self.output = self.getOutput()

        self.sweeping = self.getSweeping()
        self.amplitude = self.getAmplitude()
        self.period = self.getPeriod()

        self.lockin = self.getLocking()
        self.lockin_amplitude = self.getLockinAmplitude()
        self.lockin_frequency = self.getLockinFrequency()

        self.cv_time = 1.0

        self.case = -2
        self.before = 0
        self.start_value = 0

        self.old_start = 0
        self.old_case = -2
        
        self.startstop_dtype = [
            ('path', 'U128'),
            ('start', 'i8'),
            ('stop', 'i8'),
            ('case', 'i4'),
            ]
        
        self.startstop = np.array([], dtype=self.startstop_dtype)

    def open(self):
        """Opens connection to ADwin."""
        self.inst = ADwin()
        self.inst.Boot(os.path.join(os.path.dirname(__file__), "adwin/ADwin11.btl"))
        self.inst.Load_Process(os.path.join(os.path.dirname(__file__), "adwin/adwingold2_v4.TB0"))
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
            "output": self.output,
            "sweeping": self.sweeping,
            "amplitude": self.amplitude,
            "period": self.period,
            "lockin": self.lockin,
            "lockin_amplitude": self.lockin_amplitude,
            "lockin_frequency": self.lockin_frequency,
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
        data = self.collecting_data()
        data['start_stops'] = self.get_startstop(data)
        return data

    def collecting_data(self):
        """Collects data
        """        
        with self.lock:
            l = [
                self.inst.Fifo_Full(FifoNo=1),
                self.inst.Fifo_Full(FifoNo=2),
                self.inst.Fifo_Full(FifoNo=3),
                self.inst.Fifo_Full(FifoNo=4),
                self.inst.Fifo_Full(FifoNo=5),
                self.inst.Fifo_Full(FifoNo=6),
                self.inst.Fifo_Full(FifoNo=8),
                self.inst.Fifo_Full(FifoNo=9),
                    ]

        l = list(map(int, l))
        count = min(l)
        if count <= 0:
            return None

        with self.lock:
            V1 = self.inst.GetFifo_Double(FifoNo=1, Count=count)
            V2 = self.inst.GetFifo_Double(FifoNo=2, Count=count)

            X1 = self.inst.GetFifo_Double(FifoNo=3, Count=count)
            X2 = self.inst.GetFifo_Double(FifoNo=4, Count=count)
            Y1 = self.inst.GetFifo_Double(FifoNo=5, Count=count)
            Y2 = self.inst.GetFifo_Double(FifoNo=6, Count=count)

            trigger = np.array(self.inst.GetFifo_Double(FifoNo=8, Count=count), dtype='int')
            times = np.array(self.inst.GetFifo_Double(FifoNo=9, Count=count), dtype='float64') + self._time_offset
            
        return {
            "time": list(times),
            "V1": list(V1),
            "V2": list(V2),
            "X1": list(X1),
            "X2": list(X2),
            "Y1": list(Y1),
            "Y2": list(Y2),
            "trigger": list(trigger),
        }

    def get_startstop(self, data):
        """Get Starts and Stops
        """        
        trig = data['trigger']
        tim = data['time']
        # val = data['V1']

        # initialize new return values
        starts = []
        cases = []
        times = []
        # values = []

        # if changed trigger state
        # or if not-sweeping and more time than self.cv_time is elapsed
        for i, t in enumerate(trig):
            test1 = (self.case != t)
            test2 = (t <= 0)
            test3 = (tim[i] - self.before >= self.cv_time)
            if test1 or (test2 and test3):
                # change values to actual values
                self.case = t
                self.before = tim[i]

                # append to return values
                temp = i+self.start_value
                cases.append(self.case)
                starts.append(temp)

                # times.append(tim[i])
                # values.append(val[i])

        return {
            'times': times, 
            'starts': starts, 
            'cases': cases,
            # 'values': values,
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
        """Save data to hdf5 through a gateway. Overwrite this method if you want to change how or
        where this driver saves it data when being measured.
        
        Parameters
        ----------
        hdf5_path : str
            base hdf5_path under which you should save the data
        array
            data to save
        dgw : DataGateway
            gateway to the dataserver
        """
        
        if array is None:
            return
        
        if array['start_stops']['starts']:
            starts = array['start_stops']['starts']
            cases = array['start_stops']['cases']
            # times = array['start_stops']['times']
            # values = array['start_stops']['values']
            array.pop('start_stops')

            for i, s in enumerate(starts):
                if self.old_case != -2: # skip default entry
                    startstop_path = f"{STATUS_NAME}{CALC_NAME}{STARTSTOP_NAME}"
                    
                    x = np.array([(hdf5_path, self.old_start, s-1, self.old_case)],
                                    dtype=self.startstop_dtype)

                    self.startstop = np.append(self.startstop, x)

                    # startstop_data = {
                    #                 # 'values': values[i],
                    #                 # 'time': times[i],
                    #                 'start': self.old_start,
                    #                 'stop': s-1,
                    #                 'case': self.old_case,
                    #                 # 'path': hdf5_path
                    #             }
                    # dgw.append(
                    #     startstop_path, 
                    #     startstop_data, 
                    #     **kwargs
                    #     )
                self.old_start = s
                self.old_case = cases[i]

        if self.lockin:
            lockin_path = f"{hdf5_path}/{LOCKIN_NAME}"
            lockin_data = {
                "time": array['time'],
                "X1": array['X1'],
                "X2": array['X2'],
                "Y1": array['Y1'],
                "Y2": array['Y2'],
            }
            dgw.append(
                lockin_path, 
                lockin_data, 
                max_length=int(1e5), 
                **kwargs
                )

        print('test1')
        if not self.output:
            print('test2')
            # offset_path = f"{STATUS_NAME}{CALC_NAME}{OFFSET_NAME}" 
            offset_path = f"{STATUS_NAME}{OFFSET_NAME}" 
            offset_data = {
                "time": np.mean(array['time']),
                "V1_off": np.mean(array['V1']),
                "V2_off": np.mean(array['V2']),
            }

            dgw.append(
                offset_path, 
                offset_data, 
                max_length=int(1e5), 
                **kwargs
                )

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


        self.start_value = dgw.get(adwin_path).shape[0]

    """
    Properties
    - start / stop output
    - start / stop sweep
    - start / stop lockin
    - output
    - sweeping
    - locking
    - averaging
    - ranges
    - amplitude
    - period
    - lockin_amplitude
    - lockin_frequency
    """

    def start_output(self):
        self.setOutput(True)
            
    def stop_output(self):
        self.setOutput(False)
        
    def start_sweep(self):
        self.setSweeping(True)
            
    def stop_sweep(self):
        self.setSweeping(False)
        
    def start_lockin(self):
        self.setLocking(True)
            
    def stop_lockin(self):
        self.setLocking(False)
        
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

    def setLocking(self, value:bool):
        logger.debug('%s.setLocking(%i)', self._name, value)
        with self.lock:
            self.inst.Set_Par(Index=12, Value=int(value))
        self.lockin = self.getLocking()

    def getLocking(self):
        logger.debug('%s.getLocking()', self._name)
        with self.lock:
            return bool(self.inst.Get_Par(12))

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
        
    def setLockinAmplitude(self, value:float):
        logger.debug('%s.setLockinAmplitude(%i)', self._name, value)
        with self.lock:
            self.inst.Set_FPar(Index=12, Value=value)
        self.lockin_amplitude = self.getLockinAmplitude()

    def getLockinAmplitude(self):
        logger.debug('%s.getLockinAmplitude()', self._name)
        with self.lock:
            return float(self.inst.Get_FPar(12))
        
    def setLockinFrequency(self, value:float):
        logger.debug('%s.setLockinFrequency(%i)', self._name, value)
        with self.lock:
            self.inst.Set_FPar(Index=11, Value=value)
        self.lockin_frequency = self.getLockinFrequency()

    def getLockinFrequency(self):
        logger.debug('%s.getLockinFrequency()', self._name)
        with self.lock:
            return float(self.inst.Get_FPar(11))

    def setCVtime(self, value:float):
        logger.debug('%s.setCVtime()', self._name)
        self.cv_time = value

    def getCVtime(self):
        logger.debug('%s.getCVtime()', self._name)
        return self.cv_time