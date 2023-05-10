"""
Driver for KEYSIGHT 34461A Digit Multimeter
"""
import time

import numpy as np

from p5control.drivers.basedriver import ThreadSafeBaseDriver

class Keysight34461A_thermometer(ThreadSafeBaseDriver):
    """Driver for the Keysight34461A. Since it is MessageBased, we can use much
    of the BaseDriver class.
    """

    def open(self):
        """Open connection to the device.
        
        Overwritten to add the termination characters and reset the device after it has been
        connected.
        """
        super().open()

        self.r_twentyfive = 1e4
        self.one_over_t_twentyfive = 1 / 298.15
        self.beta = 3975.0

        self._running = False

        self.setup_instrument()

        self.write(f'DISP:TEXT "Device ready!"')


    def setup_instrument(self):
        with self.lock:
            # setup pyvisa communication
            self._inst.write_termination = "\n"
            self._inst.read_termination = "\n"
            self._inst.timeout = 10000

            self._inst.write("*CLS") # clear status command
            self._inst.write("*RST") # reset the instrument for SCPI operation
            self._inst.query("*OPC?") # wait for the operation to complete

            self._inst.write(f"CONFigure:RESistance 100000, MAX")
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
        data = np.fromstring(data[2+int(data[1]):], sep=",", dtype='f')
        times = np.linspace(self.last_time, now, len(data), endpoint=False)

        # set time for next cycle
        self.last_time = now

        # Calculate Temperature
        temperature = self.get_temperature(data)

        self._time = np.mean(times)
        self._temperature = np.mean(temperature)

        return times, temperature

    def get_temperature(self, resistance):
        one_over_temperature = np.log(resistance / self.r_twentyfive) / self.beta + self.one_over_t_twentyfive
        return 1 / one_over_temperature - 273.15    

    def get_data(self):
        times, temperature = self.retrieve_data()

        return {
            "time": list(times),
            "T": list(temperature),
        }
    
    def get_status(self):
        
        if not self._running:
            _, _ = self.retrieve_data()

        self.write(f'DISP:TEXT "T = {self._temperature:3.2f} C"')
        return {
            "time": self._time,
            "T": self._temperature,
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

