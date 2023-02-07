#!/usr/bin/env python3

from driver.Luci10 import Luci10
from numpy import floor
from time import sleep
from threading import Thread, Event
from logging import getLogger

# mylogger = getLogger(name=__name__)
mylogger = getLogger("driver")


class FemtoDLPVA100FWorker(Thread):
    def __init__(
        self,
        name="FemtoDLPVA100F Worker",
        index=1,
        delay=0.2,
    ):
        super().__init__()
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
        mylogger.info(f"({self.name}) ... initialized!")

    def run(self):
        mylogger.info(f"({self.name}) ... is starting!")
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
            self.overload_A = not self.luci.get_status_pin5(self.index)
            self.overload_B = not self.luci.get_status_pin6(self.index)
            self.luci.led_off()

            mylogger.debug(f"({self.name}) write bytes A, B: {byte_A:b}, {byte_B:b}")

            sleep(self.delay)

        mylogger.debug(f"({self.name}) ... is stopped!")


class FemtoDLPVA100F:
    def __init__(self, name="FemtoDLPVA100F", index=1):

        self.name = name

        self.femtoThread = FemtoDLPVA100FWorker(name="FemtoDLPVA100F Worker")

        self.femtoThread.dc.set()
        self.femtoThread.low_noise.set()
        self.femtoThread.lsb_A.clear()
        self.femtoThread.msb_A.clear()
        self.femtoThread.lsb_B.clear()
        self.femtoThread.msb_B.clear()

        self.femtoThread.start()

        self.set_dc = True
        self.set_low_noise = True
        self.set_amplification_A = 10
        self.set_amplification_B = 10

        mylogger.info(f"({self.name}) ... initialized!")

    def close(self):
        while not self.femtoThread.exit_request.is_set():
            self.femtoThread.exit_request.set()
            sleep(.1)
        self.femtoThread.luci.close()
        mylogger.info(f"({self.name}) Thread closed.")

    @property
    def overload(self) -> (bool, bool):
        overload = (self.overload_A, self.overload_B)
        return overload

    @property
    def overload_A(self):
        overload_A = self.femtoThread.overload_A
        mylogger.info(f"({self.name}) overload A: {overload_A}")
        return overload_A

    @property
    def overload_B(self):
        overload_B = self.femtoThread.overload_B
        mylogger.info(f"({self.name}) overload B: {overload_B}")
        return overload_B

    @property
    def dc(self) -> bool:
        mylogger.info(f"({self.name}) DC is set to: {self.set_dc}")
        return self.set_dc

    @dc.setter
    def dc(self, dc: bool = True):
        if dc:
            self.femtoThread.dc.set()
        elif not dc:
            self.femtoThread.dc.clear()
        else:
            mylogger.warning(f"({self.name}) DC must be boolean.")
        self.set_dc = dc
        _ = self.dc

    @property
    def low_noise(self) -> bool:
        mylogger.info(f"({self.name}) Low Noise is set to: {self.set_low_noise}")
        return self.set_low_noise

    @low_noise.setter
    def low_noise(self, low_noise: bool = True):
        if low_noise:
            self.femtoThread.low_noise.set()
        elif not low_noise:
            self.femtoThread.low_noise.clear()
        else:
            mylogger.warning(f"({self.name}) Low Noise must be boolean.")
        self.set_low_noise = low_noise
        _ = self.low_noise

    @property
    def amplifications(self) -> (int, int):
        return (self.amplification_A, self.amplification_B)

    @amplifications.setter
    def amplifications(self, amp: (int, int) = (10, 10)):
        self.amplification_A = amp[0]
        self.amplification_B = amp[1]

    @property
    def amplification_A(self):
        mylogger.info(f"({self.name}) Amplification A is set to: {self.set_amplification_A}")
        return self.set_amplification_A

    @amplification_A.setter
    def amplification_A(self, amp: int = 10):
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
            mylogger.info(f"({self.name}) Amplification must be 10, 100, 1000 or 10000.")
            self.amplification_A = 10
        self.set_amplification_A = amp
        _ = self.amplification_A

    @property
    def amplification_B(self):
        mylogger.info(f"({self.name}) Amplification B is set to: {self.set_amplification_B}")
        return self.set_amplification_B

    @amplification_B.setter
    def amplification_B(self, amp: int = 10):
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
            mylogger.info(f"({self.name}) Amplification must be 10, 100, 1000 or 10000.")
            self.amplification_B = 10
        self.set_amplification_B = amp
        _ = self.amplification_B

    def get_config(self):
        config = {
            "dc": self.dc,
            "low_noise": self.low_noise,
            "exp_a": self.exp_a,
            "exp_b": self.exp_b,
        }
        mylogger.info(f"({self.name}) config: {config}")
        return config

    def set_config(
        self,
        exp_a=1,
        exp_b=1,
        dc=True,
        low_noise=True,
    ):
        self.dc = dc
        if dc:
            self.set_dc()
        else:
            self.reset_dc()

        self.low_noise = low_noise
        if low_noise:
            self.set_low_noise()
        else:
            self.reset_low_noise()

        self.set_exponent_a(exp_a=exp_a)
        self.exp_a = exp_a
        self.set_exponent_b(exp_b=exp_b)
        self.exp_b = exp_b

    def set_low_noise(self):
        self.femtoThread.low_noise.set()
        mylogger.info(f"({self.name}) low noise is set to: {True}")

    def reset_low_noise(self):
        self.femtoThread.low_noise.clear()
        mylogger.info(f"({self.name}) low noise is set to: {False}")

    def set_exponent_a(
        self,
        exp_a=1,
    ):
        if exp_a < 1:
            exp_a = 1
        if exp_a > 4:
            exp_a = 4

        if (exp_a % 2) == 0:
            self.femtoThread.lsb_A.set()
        else:
            self.femtoThread.lsb_A.clear()

        if (floor((exp_a - 1) / 2) - 1) == 0:
            self.femtoThread.msb_A.set()
        else:
            self.femtoThread.msb_A.clear()

        mylogger.info(f"({self.name}) exponent a = {exp_a}")

    def set_exponent_b(
        self,
        exp_b=1,
    ):
        if exp_b < 1:
            exp_b = 1
        if exp_b > 4:
            exp_b = 4

        if (exp_b % 2) == 0:
            self.femtoThread.lsb_B.set()
        else:
            self.femtoThread.lsb_B.clear()

        if (floor((exp_b - 1) / 2) - 1) == 0:
            self.femtoThread.msb_B.set()
        else:
            self.femtoThread.msb_B.clear()

        mylogger.info(f"({self.name}) exponent a = {exp_b}")
