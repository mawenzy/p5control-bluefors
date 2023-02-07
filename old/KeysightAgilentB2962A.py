from pyvisa import ResourceManager
from logging import getLogger
from numpy import fromstring

mylogger = getLogger("driver")
"""
TODO:
- offset

"""


class KeysightAgilentB2962A:
    def __init__(
        self,
        ip="192.168.1.113",
        name="Keysight Digit Powersource",
    ):

        rm = ResourceManager("@py")
        inst = rm.open_resource(f"TCPIP::{ip}::5025::SOCKET")
        self.inst = inst
        inst.write_termination = "\r\n"
        inst.read_termination = "\n"

        self.name = name
        self.IDN = self.idn
        self.inst.write("*CLS")
        self.inst.write("*RST")
        self.inst.query("*OPC?")
        self.base_timeout = 10
        self.inst.timeout = self.base_timeout * 1000
        mylogger.info(f"({self.name}) ... initialized!")
        #self.display()

    def display(self):
        self.inst.write(f":DISPlay:ENABle 1")
        # self.inst.write(f":DISPlay:CSET 1")
        self.inst.write(f":DISPlay:VIEW DUAL")
        self.inst.write(f":DISP:TEXT:STATe 1")
        self.inst.write(f':DISP:TEXT:DATA "{self.name}"')
        mylogger.info(f"({self.name}) Display disabled.")

    def close(self):
        self.inst.close()
        mylogger.info(f"({self.name}) Connection closed.")

    def setup_voltage_sinus_mode(self, channel=None):
        if channel is None:
            channel = [1, 2]
        for ch in channel:
            self.inst.write(f":SOURce{ch}:FUNC:MODE VOLT")
            #self.inst.write(f":SOURce{ch}:VOLTage:RANGe:AUTO OFF")
            #self.inst.write(f":SOURce{ch}:CURRent:RANGe:AUTO OFF")
            self.inst.write(f":SENSe{ch}:VOLTage:PROT 2")
            self.inst.write(f":SOURce{ch}:VOLTage:MODE ARB")
            self.inst.write(f":SOURce{ch}:ARB:FUNCtion:SHAPe SIN")
            self.inst.write(f":TRIGger{ch}:TRAN:SOURce AINT")
            self.inst.write(f":TRIGger{ch}:TRAN:COUNt 1")
        self.inst.query("*OPC?")
        mylogger.info(f"({self.name}) Voltage Sinus Mode and Source Trigger is set.")

    def setup_voltage_sensor(self, channel=None):
        if channel is None:
            channel = [1, 2]
        for ch in channel:
            self.inst.write(f':SENSe{ch}:FUNCtion:ON "VOLT"')
            self.inst.write(f":TRIGger{ch}:ACQuire:SOURce:SIGNal TIM")
        self.inst.query("*OPC?")
        mylogger.info(f"({self.name}) Voltage Sensor and Trigger is set.")

    def setup_externel_trigger_output(self, pin=1):
        self.inst.write(f":SOURce:DIGital:EXTernal{pin}:FUNCtion TOUT")
        self.inst.write(f":SOURce:DIGital:EXTernal{pin}:POLarity POS")
        self.inst.write(f":SOURce:DIGital:EXTernal{pin}:TOUTput:TYPE EDGE")
        self.inst.write(f":SOURce:DIGital:EXTernal{pin}:TOUTput:EDGE:POSition BEFore")
        self.inst.write(f":SOURce:DIGital:EXTernal{pin}:TOUTput:EDGE:WIDTh DEF")
        self.inst.write(f":SOURce1:TOUTput:SIGNal EXT{pin}")
        self.inst.write(f":SOURce{pin}:TOUTput:STATe ON")
        self.inst.query("*OPC?")
        mylogger.info(f"({self.name}) External Trigger Output is set (pin{pin}).")

    def initialize(self, channel=None):
        if channel is None:
            self.inst.write(f"INIT (@1,2)")
        else:
            self.inst.write(f"INIT (@{channel})")
        mylogger.info(f"({self.name}) Initialized!")

    def fetch_data(self, channel=None):
        if channel is None:
            voltages = str(self.inst.query(f":FETCh:ARRay:VOLTage? (@1,2)"))
            voltages = fromstring(voltages, sep=",")
            data = (voltages[::2], voltages[1::2])
        else:
            voltage = str(self.inst.query(f":FETCh:ARRay:VOLTage? (@{channel})"))
            data = fromstring(voltage, sep=",")
        mylogger.info(f"({self.name}) Data fetched.")
        return data

    @property
    def idn(self):
        self.inst.query("*OPC?")
        idn = str(self.inst.query("*IDN?"))
        mylogger.info(f"({self.name}) IDN: {idn}")
        return idn

    @property
    def timeout(self) -> float:
        timeout = self.inst.timeout / 1000
        mylogger.info(f"({self.name}) timeout: {timeout}")
        return timeout

    @timeout.setter
    def timeout(self, timeout: float):
        self.inst.timeout = int((timeout + self.base_timeout) * 1000)
        _ = self.timeout

    @property
    def errorstatus(self):
        """Get error status of the device.

        :return: Error Message of Device
        """
        err = self.inst.query("SYST:ERR?")

        mylogger.info(f"({self.name}) Error Message: {err}")
        return err

    @property
    def source_count(self) -> (int, int):
        ch = (
            int(self.inst.query(f":SOURce1:ARB:COUNt?")),
            int(self.inst.query(f":SOURce2:ARB:COUNt?")),
        )
        mylogger.info(f"({self.name}) Source Counter is: {ch}")
        return ch

    @source_count.setter
    def source_count(self, count: int):
        self.inst.write(f":SOURce1:ARB:COUNt {count}")
        self.inst.write(f":SOURce2:ARB:COUNt {count}")
        self.inst.query("*OPC?")
        _ = self.source_count

    @property
    def current_limit(self) -> (float, float):
        ch = (
            float(self.inst.query(f":SENSe1:CURRent:DC:PROTection:LEVel?")),
            float(self.inst.query(f":SENSe2:CURRent:DC:PROTection:LEVel?")),
        )
        mylogger.info(f"({self.name}) Current Limit is: {ch}")
        return ch

    @current_limit.setter
    def current_limit(self, limit: float):
        """
        :param limit: 1E-8,...1E0, 1.5, 3, 10 [A]
        """
        self.inst.write(f":SENSe1:CURRent:DC:PROTection:LEVel:BOTH {limit}")
        self.inst.write(f":SENSe2:CURRent:DC:PROTection:LEVel:BOTH {limit}")
        self.inst.query("*OPC?")
        _ = self.current_limit

    @property
    def voltage_limit(self) -> (float, float):
        ch = (
            float(self.inst.query(f":SENSe1:VOLTage:DC:PROTection:LEVel?")),
            float(self.inst.query(f":SENSe2:VOLTage:DC:PROTection:LEVel?")),
        )
        mylogger.info(f"({self.name}) Voltage Limit is: {ch}")
        return ch

    @voltage_limit.setter
    def voltage_limit(self, limit: float):
        """
        :param limit: 2E-1 ... 2E2 [V]
        """
        self.inst.write(f":SENSe1:VOLTage:DC:PROTection:LEVel:BOTH {limit}")
        self.inst.write(f":SENSe2:VOLTage:DC:PROTection:LEVel:BOTH {limit}")
        self.inst.query("*OPC?")
        _ = self.voltage_limit



    @property
    def voltage_sinus_amplitude_ch1(self) -> float:
        amplitude = float(self.inst.query(f":SOURce1:ARB:VOLTage:SINusoid:AMPLitude?"))
        mylogger.info(f"({self.name}) Voltage Sinus Amplitude (Ch1) is: {amplitude}")
        return amplitude

    @voltage_sinus_amplitude_ch1.setter
    def voltage_sinus_amplitude_ch1(self, amplitude: float):
        self.inst.write(f":SOURce1:ARB:VOLTage:SINusoid:AMPLitude {amplitude}")
        self.inst.query("*OPC?")
        _ = self.voltage_sinus_amplitude_ch1

    @property
    def voltage_sinus_amplitude_ch2(self) -> float:
        amplitude = float(self.inst.query(f":SOURce2:ARB:VOLTage:SINusoid:AMPLitude?"))
        mylogger.info(f"({self.name}) Voltage Sinus Amplitude (Ch2) is: {amplitude}")
        return amplitude

    @voltage_sinus_amplitude_ch2.setter
    def voltage_sinus_amplitude_ch2(self, amplitude: float):
        self.inst.write(f":SOURce2:ARB:VOLTage:SINusoid:AMPLitude {amplitude}")
        self.inst.query("*OPC?")
        _ = self.voltage_sinus_amplitude_ch2

    @property
    def voltage_sinus_amplitude(self) -> (float, float):
        voltage_sinus_amplitude = (
            self.voltage_sinus_amplitude_ch1,
            self.voltage_sinus_amplitude_ch2,
        )
        return voltage_sinus_amplitude

    @voltage_sinus_amplitude.setter
    def voltage_sinus_amplitude(self, voltage_sinus_amplitude: float):
        self.voltage_sinus_amplitude_ch1 = voltage_sinus_amplitude
        self.voltage_sinus_amplitude_ch2 = voltage_sinus_amplitude

    @property
    def voltage_sinus_offset_ch1(self) -> float:
        offset = float(self.inst.query(f":SOURce1:ARB:VOLTage:SINusoid:OFFSet?"))
        mylogger.info(f"({self.name}) Voltage Sinus Offset (Ch1) is: {offset}")
        return offset

    @voltage_sinus_offset_ch1.setter
    def voltage_sinus_offset_ch1(self, offset: float):
        self.inst.write(f":SOURce1:ARB:VOLTage:SINusoid:OFFSet {offset}")
        self.inst.query("*OPC?")
        _ = self.voltage_sinus_offset_ch1

    @property
    def voltage_sinus_offset_ch2(self) -> float:
        offset = float(self.inst.query(f":SOURce2:ARB:VOLTage:SINusoid:OFFSet?"))
        self.inst.query("*OPC?")
        mylogger.info(f"({self.name}) Voltage Sinus Offset (Ch2) is: {offset}")
        return offset

    @voltage_sinus_offset_ch2.setter
    def voltage_sinus_offset_ch2(self, offset: float):
        self.inst.write(f":SOURce2:ARB:VOLTage:SINusoid:OFFSet {offset}")
        self.inst.query("*OPC?")
        _ = self.voltage_sinus_offset_ch2

    @property
    def voltage_sinus_offset(self) -> (float, float):
        offset = (self.voltage_sinus_offset_ch1, self.voltage_sinus_offset_ch2)
        return offset

    @voltage_sinus_offset.setter
    def voltage_sinus_offset(self, offset: float):
        self.voltage_sinus_offset_ch1 = offset
        self.voltage_sinus_offset_ch2 = offset

    @property
    def voltage_sinus_frequency(self) -> (float, float):
        frequency = (
            float(self.inst.query(f":SOURce1:ARB:VOLTage:SINusoid:FREQuency?")),
            float(self.inst.query(f":SOURce2:ARB:VOLTage:SINusoid:FREQuency?")),
        )
        mylogger.info(f"({self.name}) Voltage Sinus Frequency is: {frequency}")
        return frequency

    @voltage_sinus_frequency.setter
    def voltage_sinus_frequency(self, frequency: float):
        self.inst.write(f":SOURce1:ARB:VOLTage:SINusoid:FREQuency {frequency}")
        self.inst.write(f":SOURce2:ARB:VOLTage:SINusoid:FREQuency {frequency}")
        self.inst.query("*OPC?")
        _ = self.voltage_sinus_frequency

    @property
    def sensor_voltage_nplc_auto(self) -> bool:
        nplc = bool(int(self.inst.query(f":SENSe1:VOLTage:DC:NPLC:AUTO?")))
        mylogger.info(f"({self.name}) Sensor Voltage NPLC AUTO is: {nplc}")
        return nplc

    @sensor_voltage_nplc_auto.setter
    def sensor_voltage_nplc_auto(self, nplc: bool):
        self.inst.write(f":SENSe1:VOLTage:DC:NPLCycles:AUTO {int(nplc)}")
        self.inst.write(f":SENSe2:VOLTage:DC:NPLCycles:AUTO {int(nplc)}")
        self.inst.query("*OPC?")
        _ = self.sensor_voltage_nplc_auto

    @property
    def sensor_voltage_nplc(self) -> float:
        nplc = float(self.inst.query(f":SENSe1:VOLTage:DC:NPLC?"))
        mylogger.info(f"({self.name}) Sensor Voltage NPLC is: {nplc}")
        return nplc

    @sensor_voltage_nplc.setter
    def sensor_voltage_nplc(self, nplc: float):
        self.inst.write(f":SENSe1:VOLTage:DC:NPLC {nplc}")
        self.inst.write(f":SENSe2:VOLTage:DC:NPLC {nplc}")
        self.inst.query("*OPC?")
        _ = self.sensor_voltage_nplc

    @property
    def sensor_voltage_aperture_auto(self) -> bool:
        nplc = bool(int(self.inst.query(f":SENSe1:VOLTage:DC:APERture:AUTO?")))
        mylogger.info(f"({self.name}) Sensor Voltage APERture AUTO is: {nplc}")
        return nplc

    @sensor_voltage_aperture_auto.setter
    def sensor_voltage_aperture_auto(self, nplc: bool):
        self.inst.write(f":SENSe1:VOLTage:DC:APERture:AUTO {int(nplc)}")
        self.inst.write(f":SENSe2:VOLTage:DC:APERture:AUTO {int(nplc)}")
        self.inst.query("*OPC?")
        _ = self.sensor_voltage_aperture_auto

    @property
    def sensor_voltage_aperture(self) -> float:
        sensor_voltage_aperture = float(self.inst.query("SENSe1:VOLTage:DC:APERture?"))
        mylogger.info(f"({self.name}) Sensor Voltage Aperture: {sensor_voltage_aperture}s")
        return sensor_voltage_aperture

    @sensor_voltage_aperture.setter
    def sensor_voltage_aperture(self, set_voltage_dc_aperture="DEF"):
        """
        just use, if you need a specific sampling rate or something
        :param set_voltage_dc_aperture ['MIN'=4e-4, 'MAX'=2, 'DEF'=2e-1] (s)
        """
        self.inst.write(f"SENSe1:VOLTage:DC:APERture {set_voltage_dc_aperture}")
        self.inst.write(f"SENSe2:VOLTage:DC:APERture {set_voltage_dc_aperture}")
        self.inst.query("*OPC?")
        _ = self.sensor_voltage_aperture

    @property
    def sensor_count(self) -> (float, float):
        count = (
            float(self.inst.query(f":TRIGger1:ACQuire:COUNt?")),
            float(self.inst.query(f":TRIGger2:ACQuire:COUNt?")),
        )
        mylogger.info(f"({self.name}) Sensor Count is: {count}")
        return count

    @sensor_count.setter
    def sensor_count(self, count: float):
        self.inst.write(f":TRIGger1:ACQuire:COUNt {count}")
        self.inst.write(f":TRIGger2:ACQuire:COUNt {count}")
        self.inst.query("*OPC?")
        _ = self.sensor_count

    @property
    def sensor_timer(self) -> (float, float):
        timer = (
            float(self.inst.query(f":TRIGger1:ACQuire:TIMer?")),
            float(self.inst.query(f":TRIGger2:ACQuire:TIMer?")),
        )
        mylogger.info(f"({self.name}) Sensor Timer is: {timer}")
        return timer

    @sensor_timer.setter
    def sensor_timer(self, timer: float):
        self.inst.write(f":TRIGger1:ACQuire:TIMer {timer}")
        self.inst.write(f":TRIGger2:ACQuire:TIMer {timer}")
        self.inst.query("*OPC?")
        _ = self.sensor_timer


"""    def setup_voltage_cv_mode(self, channel=None):
        if channel is None:
            channel = [1, 2]
        for ch in channel:
            self.inst.write(f":SOURce{ch}:FUNC:MODE VOLT")
            self.inst.write(f":SOURce{ch}:VOLTage:MODE ARB")
            self.inst.write(f":SOURce{ch}:SOUR:VOLT:TRIG 0.05")
            self.inst.write(f":TRIGger{ch}:TRAN:SOURce AINT")
            self.inst.write(f":TRIGger{ch}:TRAN:COUNt 1")
        self.inst.query("*OPC?")
        mylogger.info(f"({self.name}) Constant Voltage Mode and Source Trigger is set.")
        
    @property
    def voltage_cv_level_ch1(self) -> float:
        voltage_cv_level_ch1 = float(self.inst.query(f":SOURce1:ARB:VOLTage:SINusoid:AMPLitude?"))
        mylogger.info(f"({self.name}) Constant Voltage Level (Ch1) is: {voltage_cv_level_ch1}")
        return voltage_cv_level_ch1

    @voltage_cv_level_ch1.setter
    def voltage_cv_level_ch1(self, voltage_cv_level_ch1: float):
        self.inst.write(f":SOURce1:ARB:VOLTage:SINusoid:AMPLitude {voltage_cv_level_ch1}")
        _ = self.voltage_cv_level_ch1

    @property
    def voltage_cv_level_ch2(self) -> float:
        voltage_cv_level_ch2 = float(self.inst.query(f":SOURce2:ARB:VOLTage:SINusoid:AMPLitude?"))
        mylogger.info(f"({self.name}) Constant Voltage Level (Ch2) is: {voltage_cv_level_ch2}")
        return voltage_cv_level_ch2

    @voltage_cv_level_ch2.setter
    def voltage_cv_level_ch2(self, voltage_cv_level_ch2: float):
        self.inst.write(f":SOURce2:ARB:VOLTage:SINusoid:AMPLitude {voltage_cv_level_ch2}")
        _ = self.voltage_cv_level_ch2

    @property
    def voltage_cv_level(self) -> (float, float):
        voltage_cv_level = (
            self.voltage_cv_level_ch1,
            self.voltage_cv_level_ch2,
        )
        return voltage_cv_level

    @voltage_cv_level.setter
    def voltage_cv_level(self, voltage_cv_level: float):
        self.voltage_cv_level_ch1 = voltage_cv_level
        self.voltage_cv_level_ch2 = voltage_cv_level

"""

'''
    def setup_DC_voltage(self, voltage=(0.001, 0.0015)):
        self.inst.write(":SOURce1:FUNC:MODE VOLT")
        self.inst.write(":SOURce1:VOLT:RANG:AUTO ON")
        self.inst.write(f":SOURce1:VOlt {voltage[0]}")
        self.inst.query("*OPC?")

        self.inst.write(":SOURce2:FUNCtion:MODE VOLT")
        self.inst.write(":SOURce2:VOLTage:RANGe:AUTO ON")
        self.inst.write(f":SOURce2:VOLTage {voltage[1]}")
        self.inst.query("*OPC?")

    def start_DC_voltage(self, channel=None, running=True):
        if channel is None:
            channel = [1, 2]
        for ch in channel:
            self.inst.write(f":outp{ch} {int(running)}")
            self.inst.query("*OPC?")

    def stop_DC_voltage(self, channel=None):
        self.start_DC_voltage(channel=channel, running=False)

    def setup_spot_reading(self, channel=None, aperture=0.01):
        if channel is None:
            channel = [1, 2]
        for ch in channel:
            self.inst.write(f':SENSe{ch}:FUNCtion:ON "VOLT"')
            self.inst.write(f":SENS{ch}:VOLTage:DC:APERture {aperture}")
            self.inst.query("*OPC?")

    def get_spot_reading(self, channel=None):
        if channel is None:
            channel = [1, 2]
        utc_timer = datetime.utcnow()
        if channel == [1, 2]:
            reading = fromstring(
                self.inst.query(":MEASure:VOLTage? (@1,2)"), sep=",", dtype="float64"
            )
            reading[reading == 9.910e37] = nan
            voltage1 = nanmean(reading[::2])
            voltage2 = nanmean(reading[1::2])
            voltage = [voltage1, voltage2]
        else:
            reading = fromstring(
                self.inst.query(f":MEASure:VOLTage? (@{channel})"), sep=",", dtype="float64"
            )
            reading[reading == 9.910e37] = nan
            voltage = [nanmean(reading[::2])]
        mylogger.info(f"({self.name}) Reading: {str(utc_timer)}, {str(reading)}")
        return voltage, utc_timer

    def setup_sinus_voltage(self, channel=1, chunks=1, amplitude=0.1, frequency=1, offset=0):
        self.inst.query("*OPC?")
        self.inst.write(f":SOURce{channel}:FUNC:MODE VOLT")
        self.inst.write(f":SOURce{channel}:VOLTage:MODE ARB")
        self.inst.write(f":SOURce{channel}:ARB:COUNt {chunks}")
        self.inst.write(f":SOURce{channel}:ARB:FUNCtion:SHAPe SIN")
        self.inst.query("*OPC?")

        self.inst.write(f":SOURce{channel}:ARB:VOLTage:SINusoid:AMPLitude {amplitude}")
        self.inst.write(f":SOURce{channel}:ARB:VOLTage:SINusoid:FREQuency {frequency}")
        self.inst.write(f":SOURce{channel}:ARB:VOLTage:SINusoid:OFFSet {offset}")
        self.inst.query("*OPC?")

        self.inst.write(f":TRIGger{channel}:ARM:COUNt 1")
        self.inst.write(f":TRIGger{channel}:ARM:SOURce AINT")
        self.inst.query("*OPC?")

        self.inst.write(f":OUTPut{channel}:ON:AUTO ON")
        self.inst.query("*OPC?")

    def setup_acquire(self, channel=1, source_frequency=1, points_per_chunk=100, chunks=4):
        self.inst.write(f':SENSe{channel}:FUNCtion:ON "VOLT"')
        self.inst.write(f":SENS{channel}:VOLTage:DC:APER {1/(source_frequency*points_per_chunk)}")
        self.inst.write(f":SENS{channel}:VOLTage:DC:PROT 0.1")
        self.inst.query("*OPC?")
        self.inst.write(f":TRIGger{channel}:ACQuire:COUNt {chunks*points_per_chunk*1.1}")
        self.inst.write(f":TRIGger{channel}:ACQuire:SOURce:SIGNal INT1")
        # self.inst.write(f":TRIGger{channel}:ACQuire:TIMer {nplc}")
        self.inst.query("*OPC?")

    # def trigger_sourcexy(self, channel=1):
    #    self.inst.write(f":INITiate:IMMediate:TRANsient (@{channel})")
    #    self.inst.write(f":INITiate:IMMediate:ACQuire (@{channel})")

    def trigger_acquire(self, channel=1):
        self.inst.write(f":INITiate:IMMediate:ACQuire (@{channel})")

    def trigger_all(self):
        self.inst.write(f":INITiate:IMMediate:ALL (@1,2)")

    def set_sinus_voltage(self, amplitude=1, frequency=0.1):

        self.inst.write(f":DISPlay:CSET")
        self.inst.write(f":DISPlay:VIEW dual")
        self.inst.query("*OPC?")

        self.inst.write(f":SOURce1:FUNC:MODE VOLT")
        self.inst.write(f":SOURce1:VOLTage:MODE ARB")
        self.inst.write(f":SOURce1:ARB:COUNt 2")
        self.inst.query("*OPC?")

        self.inst.write(f":SOURce1:ARB:FUNCtion:SHAPe SIN")
        self.inst.query("*OPC?")

        self.inst.write(f":SOURce1:ARB:VOLTage:SINusoid:AMPLitude 1")
        self.inst.write(f":SOURce1:ARB:VOLTage:SINusoid:FREQuency 1")
        self.inst.query("*OPC?")

        # extra
        # self.inst.write(f":SOURce1:ARB:VOLTage:SINusoid:OFFSet 0")
        # self.inst.write(f":SOURce1:ARB:VOLTage:SINusoid:PMARKer:PHASe 90")
        # self.inst.write(f":SOURce1:ARB:VOLTage:SINusoid:PMARKer:STATe 0")
        self.inst.query("*OPC?")

        self.inst.write(f':SENSe1:FUNCtion:ON "VOLT"')
        self.inst.write(f":SENS1:VOLTage:DC:NPLCycles 0.1")
        self.inst.write(f":SENS1:VOLTage:DC:PROT 0.1")
        self.inst.query("*OPC?")

        self.inst.write(f":TRIGger1:ARM:COUNt 1")
        self.inst.write(f":TRIGger1:ARM:SOURce AINT")
        self.inst.write(f":TRIGger1:ACQuire:COUNt 3000")
        self.inst.write(f":TRIGger1:ACQuire:SOURce:SIGNal TIMer")
        self.inst.write(f":TRIGger1:ACQuire:TIMer 0.001")
        self.inst.query("*OPC?")

        self.inst.write(":OUTPut1:ON:AUTO ON")
        self.inst.query("*OPC?")

        self.inst.write(":INITiate:IMMediate:TRANsient (@1)")
        self.inst.write(":INITiate:IMMediate:ACQuire (@1)")
        self.inst.query("*OPC?")
        dings = str(self.inst.query(":FETCh:ARRay:VOLTage? (@1)"))

        import numpy as np

        dings = np.fromstring(dings, sep=",")
        import matplotlib.pyplot as plt

        plt.figure(1)
        plt.plot(dings)
        plt.show()

    @property
    def trigger_count(self):
        get_trigger_count = float(self.inst.query("TRIGger:COUNt?"))
        mylogger.info(f"({self.name}) Trigger Count: {get_trigger_count}")
        return get_trigger_count

    @trigger_count.setter
    def trigger_count(self, set_trigger_count="DEF"):
        """
        :param set_trigger_count [1('MIN','DEF') to 1e6('MAX'), 'INFinity']
        """
        self.inst.write(f"TRIGger:COUNt {set_trigger_count}")
        mylogger.info(f"({self.name}) Trigger Count set to: {set_trigger_count}")

    @property
    def trigger_delay(self):
        get_trigger_delay = float(self.inst.query("TRIGger:DELay?"))
        mylogger.info(f"({self.name}) Trigger Delay: {get_trigger_delay}")
        return get_trigger_delay

    @trigger_delay.setter
    def trigger_delay(self, set_trigger_delay="DEF"):
        """
        :param set_trigger_delay [0('MIN') to 1('DEF') to 3.6e3('MAX'), 'INFinity']
        """
        self.inst.write(f"TRIGger:DELay {set_trigger_delay}")
        mylogger.info(f"({self.name}) Trigger Delay set to: {set_trigger_delay}")

    @property
    def trigger_source(self):
        get_trigger_source = self.inst.query("TRIGger:SOURce?")
        mylogger.info(f"({self.name}) Trigger Source: {get_trigger_source}")
        return get_trigger_source

    @trigger_source.setter
    def trigger_source(self, set_trigger_source="IMMediate"):
        """
        :param set_trigger_source ['IMMediate','BUS','EXTernal','INTernal']
        """
        self.inst.write(f"TRIGger:SOURce {set_trigger_source}")
        mylogger.info(f"({self.name}) Trigger Source set to: {set_trigger_source}")



    @property
    def voltage_dc_nplc(self):
        get_voltage_dc_nplc = float(self.inst.query("SENSe:VOLTage:DC:NPLC?"))
        mylogger.info(f"({self.name}) DC NPLC: {get_voltage_dc_nplc}")
        return get_voltage_dc_nplc

    @voltage_dc_nplc.setter
    def voltage_dc_nplc(self, set_voltage_dc_nplc="DEF"):
        """
        get voltage DV number of PLC (power line cycles)
        :param set_voltage_dc_nplc
        :return: get_voltage_dc_nplc [0.02='MIN',0.2,1,10='DEF',100='MAX']
        """
        self.inst.write(f"SENSe:VOLTage:DC:NPLC {set_voltage_dc_nplc}")
        mylogger.info(f"({self.name}) DC NPLC set to: {set_voltage_dc_nplc}")


'''
