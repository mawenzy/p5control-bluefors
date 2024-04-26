import logging
import time

from time import sleep

from p5control.drivers.basedriver import BaseDriver

logger = logging.getLogger(__name__)

from time import sleep
from ctypes import cdll, c_char_p, c_int, byref
from os import add_dll_directory

from threading import Thread, Event

add_dll_directory("C:\\Users\\BlueFors\\Documents\\p5control-bluefors\\core\\drivers_v2\\external")
# driver for luci interface has to be in the same directory or give the path

# untested yet since:
# decrapted overload
# simplifies configuration
# femto.py and femto_BA.py are obsolete then.

class Luci10:
    def __init__(self, name="LUCY_10"):
        logger.info('%s.__init__()', name)
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

    def led_off(self):
        self.luci.LedOff(self.index)

    def list_adapters(self):
        """Prints a list of found interfaces
        index = 1 : One Adapter found.
        index = 0 : no Adapter found.
        Adapter ID, wichtig falls mehrere LUCI Kabel verwendet werden
        """
        chr_buffer = c_char_p(b"0000")
        string = "no adapters found!"
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
                    check = check + 1
        return string

    def write_bytes(self, index, low, high):
        """Writes low and high byte to port (25:10)"""
        return self.luci.WriteData(index, low, high)

class FemtoWorker(Thread):
    def __init__(
        self,
        name,
        index=1,
        delay=.1,
    ):
        logger.info('%s.__init__()', name)
        super().__init__()

        self._name = name
        self._address = index

        self.exit_request = Event()
        self.dc = Event()
        self.low_noise = Event()
        self.lsb_A = Event()
        self.msb_A = Event()
        self.lsb_B = Event()
        self.msb_B = Event()

        self.name = name
        self.luci = Luci10()
        self.index = index
        self.delay = delay

        logger.info('opened resource "%s" at index "%s"', self._name, self._address)


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
            self.luci.led_off()

            sleep(self.delay)
        logger.info('%s stopped.', self._name)

class Femto(BaseDriver):
    def __init__(
            self, 
            name: str, 
            config='AB'
            ):
        logger.info('%s.__init__()', name)
        self._name = name
        if (config == 'AB') or (config == 'BA'):
            self.config = config
        else:
            logger.error("%s.__init__() config must be either 'AB' or 'BA'", self._name)
        self.open()

    def open(self):
        logger.info('%s.open()', self._name)

        self.femtoThread = FemtoWorker(
            name=f"{self._name}Worker", 
            )
        
        self.femtoThread.dc.set()
        self.femtoThread.low_noise.set()
        self.femtoThread.lsb_A.clear()
        self.femtoThread.msb_A.clear()
        self.femtoThread.lsb_B.clear()
        self.femtoThread.msb_B.clear()

        self.femtoThread.start()

        self.amp_A = 0
        self.amp_B = 0

        self.set_dc(True)
        self.set_low_noise(True)
        self.set_amp(10, 'A')
        self.set_amp(10, 'B')

    def close(self):
        logger.info('%s.close()', self._name)

        while not self.femtoThread.exit_request.is_set():
            self.femtoThread.exit_request.set()
            sleep(.1)
        self.femtoThread.luci.close()

    def get_status(self):
        logger.info('%s.get_status()', self._name)
        return {
            "amp_A": self.amp_A,
            "amp_B": self.amp_B,
            "dc": self.dc,
            "low_noise": self.low_noise,
        }
    

    def get_data(self):
        logger.info('%s.get_data()', self._name)
        return {
            "time": time.time(),
            "amp_A": self.amp_A,
            "amp_B": self.amp_B,
        }
    
    def set_dc(self, dc: bool = True):
        logger.info('%s.set_dc()', self._name)
        if dc:
            self.femtoThread.dc.set()
        else:
            self.femtoThread.dc.clear()
        self.dc = dc

    def get_dc(self):
        logger.info('%s.get_dc()', self._name)
        return self.dc
    
    def set_low_noise(self, low_noise: bool = True):
        logger.info('%s.set_low_noise()', self._name)
        if low_noise:
            self.femtoThread.low_noise.set()
        else:
            self.femtoThread.low_noise.clear()
        self.low_noise = low_noise

    def get_low_noise(self):
        logger.info('%s.get_low_noise()', self._name)
        return self.low_noise
    
    def set_amp(
            self, 
            amp: int = 10, 
            channel = 'A', 
            ):
        logger.info('%s.set_amp()', self._name)
        
        if self.config == 'AB':
            if channel == 'A':
                self.amp_A = amp
                self.set_amplification_A(amp)
            elif channel == 'B':
                self.amp_B = amp
                self.set_amplification_B(amp)
            else:
                logger.warning("%s.set_amp(%s, channel=%s) channel must be either 'A' or 'B'.", self._name, amp, channel)
        elif self.config == 'BA':
            if channel == 'A':
                self.amp_A = amp
                self.set_amplification_B(amp)
            elif channel == 'B':
                self.amp_B = amp
                self.set_amplification_A(amp)
            else:
                logger.warning("%s.set_amp(%s, channel=%s) channel must be either 'A' or 'B'.", self._name, amp, channel)

    def get_amp(self, channel='A'):
        logger.info('%s.get_amp()', self._name)
        if channel == 'A':
            return self.amp_A     
        elif channel == 'B':
            return self.amp_A        
        else:
            logger.warning("%s.set_amp(%s, channel=%s) channel must be either 'A' or 'B'.", self._name, amp, channel)
    
    def set_amplification_A(self, amp: int = 10):
        logger.info('%s.set_amplification_A()', self._name)
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
    
    def set_amplification_B(self, amp: int = 10):
        logger.info('%s.set_amplification_B()', self._name)
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
