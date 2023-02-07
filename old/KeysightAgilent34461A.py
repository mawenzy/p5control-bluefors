from pyvisa import ResourceManager
from numpy import fromstring
from datetime import datetime
from logging import getLogger

# mylogger = getLogger(name=__name__)
mylogger = getLogger("driver")


class KeysightAgilent34461A:
    def __init__(
        self,
        ip="192.168.1.110",
        name="Keysight Digit Multimeter",
    ):

        rm = ResourceManager("@py")
        inst = rm.open_resource(f"TCPIP0::{ip}::5025::SOCKET")
        self.inst = inst
        inst.write_termination = "\r\n"
        inst.read_termination = "\n"
        inst.timeout = 10000

        self.name = name
        self.IDN = self.idn
        self.inst.write("*CLS")
        self.inst.write("*RST")
        self.inst.query("*OPC?")

    def close(self):
        self.inst.close()
        mylogger.info(f"({self.name}) Connection closed.")

    @property
    def idn(self):
        idn = str(self.inst.query("*IDN?"))
        mylogger.info(f"({self.name}) IDN: {idn}")
        return idn

    @property
    def errorstatus(self):
        """Get error status of the device.

        :return: Error Message of Device
        """
        err = self.inst.query("SYST:ERR?")

        mylogger.info(f"({self.name}) Error Message: {err}")
        return err

    def setup_voltage_dc(self):
        self.inst.write(f"CONF:VOLT:DC")
        self.inst.write(f"SENSe:VOLTage:DC:RANGe:AUTO OFF")
        self.inst.query(f"*OPC?")
        mylogger.info(f"({self.name}) DC Voltage Mode is set.")

    def setup_immediate_trigger(self, trigger_count=1):
        self.inst.write(f"TRIG:COUN {trigger_count}")
        self.inst.write(f"TRIG:SOUR IMMediate")
        self.inst.query(f"*OPC?")
        mylogger.info(f"({self.name}) Immediate Trigger is set.")

    def setup_external_trigger(self, trigger_count=1, auto_delay="ON", slope="POS"):
        self.inst.write(f"TRIG:COUN {trigger_count}")
        self.inst.write(f"TRIG:DELay:AUTO {auto_delay}")
        self.inst.write(f"TRIG:SOUR EXT")
        self.inst.write(f"TRIG:SLOP {slope}")
        self.inst.query(f"*OPC?")
        mylogger.info(f"({self.name}) External Trigger Input is set.")

    def initialize(self):
        self.inst.write("INIT")
        mylogger.info(f"({self.name}) wait-for-trigger initialized.")

    def abort(self):
        self.inst.write("ABORt")
        mylogger.info(f"({self.name}) wait-for-trigger aborted.")

    @property
    def fetch_data(self):
        voltage = str(self.inst.query(f"FETCh?"))
        voltage = fromstring(voltage, sep=",")
        mylogger.info(f"({self.name}) Data fetched.")
        return voltage

    @property
    def get_reading(self):
        """get readings from device.

        :return: Device reading
        """
        reading = fromstring(self.inst.query("READ?"), sep=",", dtype="float64")
        mylogger.info(f"({self.name}) Reading: {str(reading)}")
        return reading

    @property
    def sample_count(self) -> int:
        sample_count = int(self.inst.query("SAMP:COUN?"))
        mylogger.info(f"({self.name}) Sample Count: {sample_count}")
        return sample_count

    @sample_count.setter
    def sample_count(self, sample_count: int):
        self.inst.write(f"SAMP:COUN {sample_count}")
        self.inst.query("*OPC?")
        _ = self.sample_count

    @property
    def voltage_dc_range(self) -> float:
        get_voltage_dc_range = float(self.inst.query("SENSe:VOLTage:DC:RANGe?"))
        mylogger.info(f"({self.name}) DC Voltage Range: {get_voltage_dc_range}V")
        return get_voltage_dc_range

    @voltage_dc_range.setter
    def voltage_dc_range(self, set_voltage_dc_range):
        """
        :param set_voltage_dc_range ['MIN'=.1,1,10,100,1000='MAX'='DEF' (V)]
        """
        self.inst.write(f"SENSe:VOLTage:DC:RANGe {set_voltage_dc_range}")
        self.inst.query("*OPC?")
        _ = self.voltage_dc_range

    @property
    def voltage_dc_aperture(self) -> float:
        get_voltage_dc_aperture = float(self.inst.query("SENSe:VOLTage:DC:APERture?"))
        mylogger.info(f"({self.name}) DC Voltage Aperture: {get_voltage_dc_aperture}s")
        return get_voltage_dc_aperture

    @voltage_dc_aperture.setter
    def voltage_dc_aperture(self, set_voltage_dc_aperture="DEF"):
        """
        just use, if you need a specific sampling rate or something
        :param set_voltage_dc_aperture ['MIN'=4e-4, 'MAX'=2, 'DEF'=2e-1] (s)
        """
        self.inst.write(f"SENSe:VOLTage:DC:APERture {set_voltage_dc_aperture}")
        self.inst.query("*OPC?")
        _ = self.voltage_dc_aperture

    @property
    def voltage_dc_resolution(self) -> float:
        get_voltage_dc_resolution = float(self.inst.query("SENSe:VOLTage:DC:RESolution?"))
        mylogger.info(f"({self.name}) DC Voltage Resolution: {get_voltage_dc_resolution}V")
        return get_voltage_dc_resolution

    @voltage_dc_resolution.setter
    def voltage_dc_resolution(self, set_voltage_dc_resolution="DEF"):
        """
        :param set_voltage_dc_resolution ['MIN'=.1,1,10,100,1000='MAX'='DEF' (V)]
        :return: get_voltage_dc_resolution
        """
        self.inst.write(f"SENSe:VOLTage:DC:RESolution {set_voltage_dc_resolution}")
        self.inst.query("*OPC?")
        _ = self.voltage_dc_resolution

    @property
    def voltage_dc_nplc(self) -> float:
        get_voltage_dc_nplc = float(self.inst.query("SENSe:VOLTage:DC:NPLC?"))
        mylogger.info(f"({self.name}) DC Voltage NPLC: {get_voltage_dc_nplc}")
        return get_voltage_dc_nplc

    @voltage_dc_nplc.setter
    def voltage_dc_nplc(self, set_voltage_dc_nplc="DEF"):
        """
        get voltage DV number of PLC (power line cycles)
        :param set_voltage_dc_nplc
        :return: get_voltage_dc_nplc [0.02='MIN',0.2,1,10='DEF',100='MAX']
        """
        self.inst.write(f"SENSe:VOLTage:DC:NPLC {set_voltage_dc_nplc}")
        self.inst.query("*OPC?")
        _ = self.voltage_dc_nplc

    '''

        
    def setup_chunk(self, source_frequency=1, nplc=0.01, chunks=4):
        self.inst.write(f"SENSe:VOLTage:DC:APERture {nplc*source_frequency}")
        # self.inst.write(f"SENSe:VOLTage:DC:NPLC {nplc}")
        self.inst.write(f"SAMP:COUN {chunks/nplc*1.2}")
        self.inst.write(f"SAMP:COUN:PRETrigger {chunks/nplc*.1}")

        self.inst.write(f"TRIG:COUN 1")
        self.inst.write(f"TRIG:DEL:AUTO ON")
        self.inst.write(f"SAMP:TIM 0.01")
        self.inst.query(f"*OPC?")
        self.inst.write(f"TRIG:SOUR EXT")
        self.inst.write(f"TRIG:SLOPe POSitive")
        self.inst.query(f"*OPC?")
        self.inst.write(f"INIT")

    def trigger_chunk(self):
        self.inst.write("INIT")

    def get_chunk(self):
        chunk = fromstring(self.inst.query("FETCh?"), sep=",", dtype="float64")
        mylogger.info(f"({self.name}) Reading: {str(chunk)}")
        return chunk
        # self.inst.write(f"")
    
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


    
    
    '''
