"""
Driver for KEYSIGHT 34461A Digit Multimeter
"""
import time
import logging

import numpy as np

from pyvisa import ResourceManager

from p5control.drivers.basedriver import ThreadSafeBaseDriver, BaseDriverError


logger = logging.getLogger(__name__)

class AMI430(ThreadSafeBaseDriver):
    """Driver for the Keysight34461A. Since it is MessageBased, we can use much
    of the BaseDriver class.
    """

    def open(self):
        """Open connection to the device.
        
        Overwritten to add the termination characters and reset the device after it has been
        connected.
        """


        rm = ResourceManager()
        self._inst = rm.open_resource(f'TCPIP::{self._address}::7180::SOCKET')

        self._inst.write_termination = u'\r\n'
        self._inst.read_termination = u'\r\n'
        self._inst.timeout=2000
        self._inst.chunk_size = 20480 #100kb

        self._running = False

        _ = self._inst.read()
        _ = self._inst.read()

        logger.info('opened resource "%s" at address "%s"', self._name, self._address)
        
        self.setup_instrument()

    def close(self):
        """Close connection to the device and reset self._inst variable to None
        
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
        self.local_control()
        self._inst.close()
        self._inst = None

    def goto_zero(self):
        logger.debug('%s.goto_zero(%f)', self._name)
        with self.lock:
            self._inst.write('ZERO')
    
    def pause(self):
        logger.debug('%s.pause(%f)', self._name)
        with self.lock:
            self._inst.write('PAUSE')
        
    def local_control(self):
        logger.debug('%s.local_control(%f)', self._name)
        with self.lock:
            self._inst.write('SYSTem:LOCal')

    def get_field(self):
        logger.debug('%s.get_field(%f)', self._name)
        return float(self._inst.query('FIELD:MAGnet?'))
    
    def set_field(self, target):
        logger.debug('%s.set_field(%f)', self._name, target)
        self._inst.write(f'CONFigure:FIELD:TARGet {target:6.5d}')
        
#### To be continued ... 

    def setup_instrument(self):
        with self.lock:
            # setup pyvisa communication
            self._inst.write_termination = "\n"
            self._inst.read_termination = "\n"
            self._inst.timeout = 10000

            self._inst.write("*CLS") # clear status command
            self._inst.write("*RST") # reset the instrument for SCPI operation
            self._inst.query("*OPC?") # wait for the operation to complete

            self._inst.write(f"CONFigure:RESistance MAX, DEF")
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

        self._time = np.mean(times)
        self._resistance = np.mean(data)

        return times, data  

    def get_data(self):
        times, resistance = self.retrieve_data()

        return {
            "time": list(times),
            "R": list(resistance),
        }
    
    def get_status(self):
        
        if not self._running:
            _, _ = self.retrieve_data()

        self.write(f'DISP:TEXT "R = {self._resistance/1000000:3.2f} MOhm"')

        return {
            "time": self._time,
            "R": self._resistance,
        }

    def _save_data(self, hdf5_path, array, dgw):
        """save data and set attributes for default values for buffers."""
        path = f"{hdf5_path}/{self._name}"
        dgw.append(
            path,
            array,
            max_length=int(10000),
            down_sample=1,
        )

