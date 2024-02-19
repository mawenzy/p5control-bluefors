"""
Driver for KEYSIGHT 34461A Digit Multimeter
"""
import time

import numpy as np

from p5control.drivers.basedriver import BaseDriver, ThreadSafeBaseDriver
from p5control import DataGateway, InstrumentGateway

class Keysight34461A_ground(ThreadSafeBaseDriver):"""
Driver for KEYSIGHT 34461A Digit Multimeter
"""
import time

import numpy as np

from p5control.drivers.basedriver import BaseDriver, ThreadSafeBaseDriver
from p5control import DataGateway, InstrumentGateway

class Keysight34461A_ground(ThreadSafeBaseDriver):
    """Driver for the Keysight34461A. Since it is MessageBased, we can use much
    of the BaseDriver class.
    """

    def open(self):
        """Open connection to the device.
        
        Overwritten to add the termination characters and reset the device after it has been
        connected.
        """
        super().open()

        self._running = False

        self._voltage = 0

        self.setup_instrument()

        self._inst.write(f'DISP:TEXT "Device ready!"')

    def setup_instrument(self):
        with self.lock:
            # setup pyvisa communication
            self._inst.write_termination = "\n"
            self._inst.read_termination = "\n"
            self._inst.timeout = 20000

            self._inst.write("*CLS") # clear status command
            self._inst.write("*RST") # reset the instrument for SCPI operation
            self._inst.query("*OPC?") # wait for the operation to complete

            # copied from messprogramm
            self._inst.write('VOLT:DC:NPLC MIN')
            #don't do autorange, else time axis doesnt work
            # self._inst.write('VOLT:DC:RANG:AUTO ON')
            self._inst.write('VOLT:DC:RANG:AUTO OFF')
            self._inst.write('VOLT:DC:RANG 100')
            self._inst.write(':SENS:VOLT:DC:ZERO:AUTO OFF')
            self._inst.write('TRIG:SOUR IMM')
            self._inst.write("TRIG:COUN INF")
            self._inst.write("SAMP:COUN MAX")
            self._inst.write("INIT")
        self.last_time = time.time()

    def start_measuring(self):
        self.last_time = time.time()
        self._running = True
    
    def stop_measuring(self):
        self._running = False
            
    def retrieve_data(self):
        with self.lock:
            # time stamp created here, after we have acquired the lock, because we now can assume
            # that the instrument will get the query with negligible delay, after which it returns
            # the data it has measured up to this point. This is important to make sure that the
            # time stamps are accurate.
            now = time.time()
            data = self._inst.query("R?")

        # see page 205 in programmer manual
        voltage = np.fromstring(data[2+int(data[1]):], sep=",", dtype='f')
        times = np.linspace(self.last_time, now, len(data), endpoint=False)

        # set time for next cycle
        self.last_time = now

        self._time = now
        if len(voltage) > 0:
            self._voltage = np.mean(voltage)
        else:
            self._voltage = 0

        return times, voltage

    def get_data(self):
        times, voltage = self.retrieve_data()

        return {
            "time": list(times),
            "T": list(voltage),
        }
    
    def get_status(self):
        
        if not self._running:
            self.retrieve_data()

        self._inst.write(f'DISP:TEXT "V = {self._voltage*1000:3.2f} mV"')
        return {
            "time": float(self._time),
            "V": float(self._voltage),
        }


    def _save_data(self, hdf5_path, array, dgw):
        """save data and set attributes for default values for buffers."""
        path = f"{hdf5_path}/{self._name}"
        dgw.append(
            path,
            array,
            max_length=int(10000),
            down_sample=int(10)
        )

