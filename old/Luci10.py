#!/usr/bin/env python3

from time import sleep
from ctypes import cdll, c_char_p, c_int, byref
from os import add_dll_directory
from logging import getLogger

add_dll_directory(r"D:\Documents\SoftMess\driver")
# driver for luci interface has to be in the same directory or give the path

# mylogger = getLogger(name=__name__)
mylogger = getLogger("driver")


class Luci10:
    def __init__(self, name="LUCY_10"):
        self.name = name
        self.index = 1
        self.luci = cdll.LoadLibrary("LUCI_10_x64.dll")
        self.luci.EnumerateUsbDevices()
        self.idn = self.list_adapters()
        self.led_on()
        sleep(1)
        self.led_off()
        mylogger.debug(f"({self.name}) ... started.")

    def close(self):
        del self.luci
        mylogger.debug(f"({self.name}) ... closed.")

    def led_on(self):
        self.luci.LedOn(self.index)
        mylogger.debug(f"({self.name}) LED on.")

    def led_off(self):
        self.luci.LedOff(self.index)
        mylogger.debug(f"({self.name}) LED off.")

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
                    mylogger.debug(f"({self.name}) {string}")
                    check = check + 1
        if check == 0:
            mylogger.debug(f"({self.name}) {string}")
        if string == old_string:
            mylogger.error(f"({self.name}) {string}")
        return string

    def write_bytes(self, index, low, high):
        """Writes low and high byte to port (25:10)"""
        return self.luci.WriteData(index, low, high)

    def get_status_pin5(self, index):
        """Returns status of input 5"""
        status = c_int(0)
        self.luci.GetStatusPin5(index, byref(status))
        status = bool(status.value)
        mylogger.debug(f"({self.name}) Pin 5: {status}")
        return status

    def get_status_pin6(self, index):
        """Returns status of input 6"""
        status = c_int(0)
        self.luci.GetStatusPin6(index, byref(status))
        status = bool(status.value)
        mylogger.debug(f"({self.name}) Pin 6: {status}")
        return status

    def get_status_pin7(self, index):
        """Returns status of input 7"""
        status = c_int(0)
        self.luci.GetStatusPin7(index, byref(status))
        status = bool(status.value)
        mylogger.debug(f"({self.name}) Pin 7: {status}")
        return status
