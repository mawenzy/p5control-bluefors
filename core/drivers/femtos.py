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
from time import sleep
from ctypes import cdll, c_char_p, c_int, byref
from os import add_dll_directory

from threading import Thread, Event
from queue import Queue

add_dll_directory("C:\\Users\\BlueFors\\Documents\\p5control-bluefors\\core\\drivers")
# driver for luci interface has to be in the same directory or give the path

class Luci10:
    def __init__(self, name="LUCY_10"):
        self.name = name
        self.index = 1

        self._name = name
        self._address = 1

        self.luci = cdll.LoadLibrary("LUCI_10_x64.dll")
        self.luci.EnumerateUsbDevices()
        self.idn = self.list_adapters()
        self.led_on()
        sleep(1)
        self.led_off()
        logger.info('opened resource "%s" at address "%s"', self._name, self._address)

    def close(self):
        del self.luci
        logger.info('closing resource "%s" at address "%s"', self._name, self._address)
        
    def led_on(self):
        self.luci.LedOn(self.index)
        logger.debug('%s.led_on()', self._name)

    def led_off(self):
        self.luci.LedOff(self.index)
        logger.debug('%s.led_off()', self._name)

    def list_adapters(self):
        """Prints a list of found interfaces
        index = 1 : One Adapter found.
        index = 0 : no Adapter found.
        Adapter ID, wichtig falls mehrere LUCI Kabel verwendet werden
        """
        chr_buffer = c_char_p(b"0000")
        string = "no adapters found!"
        old_string = string
        check = 0
        for i in range(256):
            if self.luci.GetProductString(i, chr_buffer, 49) == 0:
                self.index = i
                temp = c_int(0)
                self.luci.ReadAdapterID(i, byref(temp))
                temp = temp.value
                name = chr_buffer.value.decode("utf-8")
                string = "index: %i, name: %s, ID: %i" % (i, name, temp)
                if check >= 0:
                    logger.debug('%s.list_adapters() = %s', self._name, string)
                    check = check + 1
        if check == 0:
            logger.debug('%s.list_adapters() = %s', self._name, string)
        if string == old_string:
            logger.debug('%s.list_adapters() = %s', self._name, string)
        return string

    def write_bytes(self, index, low, high):
        """Writes low and high byte to port (25:10)"""
        
        logger.debug('%s.write_bytes(%s, %s, %s)', self._name, index, low, high)
        return self.luci.WriteData(index, low, high)

    def get_status_pin5(self, index):
        """Returns status of input 5"""
        status = c_int(0)
        self.luci.GetStatusPin5(index, byref(status))
        status = bool(status.value)
        logger.debug('%s.get_status_pin5(%i) = %s', self._name, index, status)
        return status

    def get_status_pin6(self, index):
        """Returns status of input 6"""
        status = c_int(0)
        self.luci.GetStatusPin6(index, byref(status))
        status = bool(status.value)
        logger.debug('%s.get_status_pin6(%i) = %s', self._name, index, status)
        return status

    def get_status_pin7(self, index):
        """Returns status of input 7"""
        status = c_int(0)
        self.luci.GetStatusPin7(index, byref(status))
        status = bool(status.value)
        logger.debug('%s.get_status_pin7(%i) = %s', self._name, index, status)
        return status


class FemtoDLPVA100BWorker(Thread):
    def __init__(
        self,
        name,
        queue,
        index=1,
        delay=0.2,
    ):
        super().__init__()

        self._name = name
        self._address = index

        self.queue = queue
        self.exit_request = Event()
        self.dc = Event()
        self.low_noise = Event()
        self.lsb_A = Event()
        self.msb_A = Event()
        self.lsb_B = Event()
        self.msb_B = Event()

        self.overload_A = False
        self.overload_B = False

        self.name = name
        self.luci = Luci10()
        self.index = index
        self.delay = delay

        logger.info('opened resource "%s" at address "%s"', self._name, self._address)


    def run(self):
        logger.info('%s is running.', self._name)

        while not self.exit_request.is_set():

            byte_A, byte_B = 0, 0
            if self.lsb_A.is_set():
                byte_A |= 0b00000010  # Set 2nd bit to 1
            if self.msb_A.is_set():
                byte_A += 4
            if self.lsb_B.is_set():
                byte_B += 2
            if self.msb_B.is_set():
                byte_B += 4
            if self.dc.is_set():
                byte_A += 8
                byte_B += 8
            if self.low_noise.is_set():
                byte_A += 16
                byte_B += 16

            self.luci.led_on()
            self.luci.write_bytes(self.index, byte_A, byte_B)
            now = time.time()
            self.overload_A = not self.luci.get_status_pin5(self.index)
            self.overload_B = not self.luci.get_status_pin6(self.index)
            self.luci.led_off()

            self.queue.put(
                {'time': now,
                 'overload_A': self.overload_A,
                 'overload_B': self.overload_B,
                    }
                )


            sleep(self.delay)

        logger.info('%s stopped.', self._name)

class FemtoDLPVA100B(BaseDriver):
    """Represents an instrument which magically measures a sine wave. Both the frequency and the amplitude can be changed.

    Parameters
    ----------
    name : str
        name for this instance
    """

    def __init__(self, name: str):
        self._name = name
        self.open()

    def open(self):
        logger.debug(f'{self._name}.open()')

        self.queue = Queue()
        self.femtoThread = FemtoDLPVA100BWorker(
            name=f"{self._name}Worker", 
            queue=self.queue
            )

        self.femtoThread.dc.set()
        self.femtoThread.low_noise.set()
        self.femtoThread.lsb_A.clear()
        self.femtoThread.msb_A.clear()
        self.femtoThread.lsb_B.clear()
        self.femtoThread.msb_B.clear()

        self.femtoThread.start()

        self.set_dc(True)
        self.set_low_noise(True)
        self.set_amplification_A(1000)
        self.set_amplification_B(1000)

    def close(self):
        logger.debug(f'{self._name}.close()')

        while not self.femtoThread.exit_request.is_set():
            self.femtoThread.exit_request.set()
            sleep(.1)
        self.femtoThread.luci.close()

    def get_status(self):
        """Returns the current amplitude and frequency."""
        return {
            "amp_A": self.amplification_A,
            "amp_B": self.amplification_B,
            "overload_A": self.femtoThread.overload_A,
            "overload_B": self.femtoThread.overload_B,
            "dc": self.dc,
            "low_noise": self.low_noise,
        }
    

    def get_data(self):
        """Calculates sine wave over the time passed since the
        last call and adds some noise to it.
        """
        logger.debug(f'{self._name}.get_data()')

        times, overload_A, overload_B = [], [], []

        while not self.queue.empty():
            element = self.queue.get()
            times.append(element['time'])
            overload_A.append(element['overload_A'])
            overload_B.append(element['overload_B'])
            self.queue.task_done()

        self.overload_A = False
        self.overload_B = False

        if np.sum(overload_A) > 0:
            self.overload_A = True
        if np.sum(overload_B) > 0:
            self.overload_B = True           

        logger.debug('%s.get_data() %s', self._name, f'{len(times)}, {len(overload_A)}, {len(overload_B)}')

        return {
            "time": list(times),
            "overload_A": list(overload_A),
            "overload_B": list(overload_B),
        }
    
    
    def _save_data(self, hdf5_path, array, dgw):
        """save data and set attributes for default values for buffers."""
        path = f"{hdf5_path}/{self._name}"
        if len(array['time'])>0:
            dgw.append(
                path,
                array
            )
    
    def set_dc(self, dc: bool = True):
        if dc:
            self.femtoThread.dc.set()
        else:
            self.femtoThread.dc.clear()
        self.dc = dc

    def get_dc(self):
        return self.dc
    
    def set_low_noise(self, low_noise: bool = True):
        if low_noise:
            self.femtoThread.low_noise.set()
        else:
            self.femtoThread.low_noise.clear()
        self.low_noise = low_noise

    def get_low_noise(self):
        return self.low_noise
    
    def set_amplification_A(self, amp: int = 10):
        if amp == 10000:
            self.femtoThread.lsb_A.set()
            self.femtoThread.msb_A.set()
        elif amp == 1000:
            self.femtoThread.lsb_A.clear()
            self.femtoThread.msb_A.set()
        elif amp == 100:
            self.femtoThread.lsb_A.set()
            self.femtoThread.msb_A.clear()
        elif amp == 10:
            self.femtoThread.lsb_A.clear()
            self.femtoThread.msb_A.clear()
        else:
            logger.warning("%s.set_amplification_A(%s) Amplification must be 10, 100, 1000 or 10000.", self._name, amp)
            self.set_amplification_A(10)
        self.amplification_A = amp

    def get_amplification_A(self):
        return self.amplification_A
    
    def set_amplification_B(self, amp: int = 10):
        if amp == 10000:
            self.femtoThread.lsb_B.set()
            self.femtoThread.msb_B.set()
        elif amp == 1000:
            self.femtoThread.lsb_B.clear()
            self.femtoThread.msb_B.set()
        elif amp == 100:
            self.femtoThread.lsb_B.set()
            self.femtoThread.msb_B.clear()
        elif amp == 10:
            self.femtoThread.lsb_B.clear()
            self.femtoThread.msb_B.clear()
        else:
            logger.warning("%s.set_amplification_B(%s) Amplification must be 10, 100, 1000 or 10000.", self._name, amp)
            self.set_amplification_B(10)
        self.amplification_B = amp

    def get_amplification_B(self):
        return self.amplification_B
