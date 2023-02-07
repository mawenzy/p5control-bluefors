from pyvisa import ResourceManager
from numpy import fromstring
from datetime import datetime
from time import sleep
import numpy as np
import matplotlib.pyplot as plt


from logging import getLogger
from driver.KeysightAgilent34461A import KeysightAgilent34461A
from driver.KeysightAgilentB2962A import KeysightAgilentB2962A
from json import load
from datetime import datetime
from numpy import floor

mylogger = getLogger("driver")

"""
Incorporate:
- femto
- setup
- Lock-in
"""


class Chunks:
    def __init__(
        self,
        multi1=KeysightAgilent34461A(ip="192.168.1.110", name="Keysight Digital Multimeter 1"),
        multi2=KeysightAgilent34461A(ip="192.168.1.111", name="Keysight Digital Multimeter 2"),
        source=KeysightAgilentB2962A(ip="192.168.1.113", name="Keysight Digital Powersource 1"),
        name="Chunks",
    ):
        self.name = name
        self.multi1 = multi1
        self.multi2 = multi2
        self.source = source
        self.synchro_path = "driver/chunk_spezifications.json"

        self.set_mode = "fast"
        self.synchro = self.get_synchro(self.set_mode)
        self.sensor_delay = self.synchro["sensor_delay"]
        self.set_chunks = 1

        self.offsets = (0,0)
        self.offsets_times = (0,0)

        mylogger.info(f"({self.name}) ... initilized!")

    def get_synchro(self, mode):
        """
        Keep in mind, that False/True have to be minor letters in json file
        :param mode: search word
        :return: spezification corresponding to mode
        """
        with open(self.synchro_path, "r") as file:
            dicts = load(file)
        synchro = [s for s in dicts if s["mode"] == mode]
        return synchro[0]

    def setup(self):
        self.source.setup_voltage_sinus_mode()
        self.source.setup_voltage_sensor()
        self.source.setup_externel_trigger_output()
        for multi in [self.multi1, self.multi2]:
            multi.setup_voltage_dc()
            multi.setup_external_trigger()

    @property
    def get(self):
        self.multi1.initialize()
        self.multi2.initialize()
        sleep(.1)
        start_time = datetime.utcnow()
        self.source.initialize()

        V_source_1, V_source_2 = self.source.fetch_data()
        stop_time = datetime.utcnow()
        sleep(.1)
        V_sample_1 = self.multi1.fetch_data
        V_sample_2 = self.multi2.fetch_data
        V_source_1 = V_source_1[self.synchro["sensor_delay"]:]
        V_source_2 = V_source_2[self.synchro["sensor_delay"]:]
        data = {
            "V_sample_1": V_sample_1,
            "V_sample_2": V_sample_2,
            "V_source_1": V_source_1,
            "V_source_2": V_source_2,
            "start_time": start_time,
            "stop_time": stop_time,
        }
        return data

    @property
    def config(self) -> dict:
        config = {
            "__synchro__": "_______",
            "mode": self.mode,
            "chunks": self.chunks,
            "source_frequency": self.source.voltage_sinus_frequency,
            "source_sensor_voltage_nplc_auto": self.source.sensor_voltage_nplc_auto,
            "source_sensor_voltage_nplc": self.source.sensor_voltage_nplc,
            "source_sensor_voltage_aperture_auto": self.source.sensor_voltage_aperture_auto,
            "source_sensor_voltage_aperture": self.source.sensor_voltage_aperture,
            "source_sensor_count": self.source.sensor_count,
            "source_sensor_timer": self.source.sensor_timer,
            "source_sensor_delay": self.sensor_delay,
            "sensor_voltage_dc_nplc": (self.multi1.voltage_dc_nplc, self.multi2.voltage_dc_nplc),
            "sensor_voltage_dc_resolution": (
                self.multi1.voltage_dc_resolution,
                self.multi2.voltage_dc_resolution,
            ),
            "sensor_voltage_dc_aperture": (
                self.multi1.voltage_dc_aperture,
                self.multi2.voltage_dc_aperture,
            ),
            "sensor_sample_count": (self.multi1.sample_count, self.multi2.sample_count),
            "__levels__": "_______",
            "source_amplitude": self.source_amplitude,
            "source_offset": self.source_offset,
            "sample_range": self.sample_range
        }
        return config


    def plot(self, data):
        plt.figure(0)
        plt.plot(data["V_sample_1"], ".", label="V_sample_1")
        plt.plot(data["V_sample_2"], ".", label="V_sample_2")
        plt.plot(data["V_source_1"], ".", label="V_source_1")
        plt.plot(data["V_source_2"], ".", label="V_source_2")
        plt.legend()
        plt.show()

    @property
    def sample_range(self) -> (float, float):
        return (self.sample_range_1, self.sample_range_2)

    @sample_range.setter
    def sample_range(self, sample_range: float):
        self.sample_range_1 = sample_range
        self.sample_range_2 = sample_range

    @property
    def sample_range_1(self) -> float:
        return self.multi1.voltage_dc_range

    @sample_range_1.setter
    def sample_range_1(self, sample_range_1: float):
        self.multi1.voltage_dc_range = sample_range_1

    @property
    def sample_range_2(self) -> float:
        return self.multi2.voltage_dc_range

    @sample_range_2.setter
    def sample_range_2(self, sample_range_2: float):
        self.multi2.voltage_dc_range = sample_range_2

    @property
    def mode(self) -> str:
        return self.synchro["mode"]

    @mode.setter
    def mode(self, mode: str = "fast"):
        synchro = self.get_synchro(mode)
        self.synchro = synchro
        self.set_mode = mode
        chunks = self.chunks
        self.sensor_delay = synchro["sensor_delay"]

        self.source.source_count = chunks
        self.source.voltage_sinus_frequency = synchro["source_frequency"]

        self.source.sensor_voltage_aperture_auto = synchro["sensor_voltage_aperture_auto"]
        self.source.sensor_voltage_aperture = synchro["sensor_voltage_aperture"]
        self.source.sensor_count = floor(synchro["sensor_count"] * chunks) + synchro["sensor_delay"]
        self.source.sensor_timer = synchro["sensor_timer"]
        self.source.timeout = synchro["sensor_count"] * chunks * synchro["sensor_timer"]

        for i, multi in enumerate([self.multi1, self.multi2]):
            multi.voltage_dc_aperture = synchro["voltage_dc_aperture"]
            multi.sample_count = floor(synchro["sample_count"] * chunks)
        mylogger.info(f"({self.name}) Mode set to {mode}.")

    @property
    def chunks(self) -> str:
        return self.set_chunks

    @chunks.setter
    def chunks(self, chunks: int = 1):
        synchro = self.synchro
        if chunks > synchro["max_chunks"]:
            chunks = synchro["max_chunks"]
            mylogger.info(f"({self.name}) Too much Chunks.")

        self.set_chunks = chunks
        self.source.source_count = chunks
        self.source.sensor_count = floor(synchro["sensor_count"] * chunks) + synchro["sensor_delay"]
        self.source.timeout = synchro["sensor_count"] * chunks * synchro["sensor_timer"]
        for i, multi in enumerate([self.multi1, self.multi2]):
            multi.sample_count = floor(synchro["sample_count"] * chunks)
        mylogger.info(f"({self.name}) Chunks set to {chunks}.")

    @property
    def source_amplitude(self) -> (float, float):
        source_amplitude = self.source.voltage_sinus_amplitude
        return source_amplitude

    @source_amplitude.setter
    def source_amplitude(self, source_amplitude: float):
        self.source.voltage_sinus_amplitude_ch1 = source_amplitude
        self.source.voltage_sinus_amplitude_ch2 = -source_amplitude

    @property
    def source_offset(self) -> (float, float):
        source_offset = self.source.voltage_sinus_offset
        return source_offset

    @source_offset.setter
    def source_offset(self, source_offset: float):
        self.source.voltage_sinus_offset = source_offset


"""

    def setup_synchro(self, mode="fast", chunks=10):
        synchro = self.get_synchro(mode)
        self.synchro = synchro
        self.mode = mode
        self.chunks = chunks

        self.source.setup_voltage_sinus_mode()
        self.source.source_count = synchro["source_count"] * chunks
        self.source.voltage_sinus_frequency = synchro["source_frequency"]

        self.source.setup_voltage_sensor()
        self.source.sensor_voltage_aperture_auto = synchro["sensor_voltage_aperture_auto"]
        self.source.sensor_voltage_aperture = synchro["sensor_voltage_aperture"]
        self.source.sensor_count = ceil(synchro["sensor_count"] * chunks)
        self.source.sensor_timer = synchro["sensor_timer"]
        self.source.timeout = synchro["sensor_count"] * chunks * synchro["sensor_timer"]

        self.source.setup_externel_trigger_output()

        for i, multi in enumerate([self.multi1, self.multi2]):
            multi.setup_voltage_dc()
            multi.voltage_dc_aperture = synchro["voltage_dc_aperture"]
            multi.sample_count = synchro["sample_count"] * chunks
            multi.setup_external_trigger()
        return synchro

        self.source.voltage_sinus_offset = synchro["source_offset"]
        for i, multi in enumerate([self.multi1, self.multi2]):
            multi.voltage_dc_range = synchro["voltage_dc_range"][i]

        self.source_amplitude = 0.1
        self.source_offset = 0
        
    def setup(self, mode="fast"):
        synchro = self.get_synchro(mode)
        self.synchro = synchro
        self.source.voltage_sinus_offset = synchro["source_offset"]
        for i, multi in enumerate([self.multi1, self.multi2]):
            multi.voltage_dc_range = synchro["voltage_dc_range"][i]
"""
"""


        self.source.inst.write(f":SOURce1:ARB:VOLTage:SINusoid:PMARker:STATe ON")
        self.source.inst.write(f":SOURce1:ARB:VOLTage:SINusoid:PMARker:SIGNal EXT8")
        self.source.inst.write(f":SOURce1:ARB:VOLTage:SINusoid:PMARker:PHase 90")


        self.source.inst.write(f":SOURce1:TOUTput:SIGNal EXT1")
        print(self.source.inst.query(f":SOURce1:TOUTput:SIGNal?"))
        self.source.inst.write(f":SOURce1:TOUTput:STATe ON")
        print(self.source.inst.query(f":SOURce1:TOUTput:STATe?"))

        self.source.inst.write(f":SENSe1:TOUTput:SIGNal EXT1")
        print(self.source.inst.query(f":SENSe1:TOUTput:SIGNal?"))
        self.source.inst.write(f":SENSe1:TOUTput:STATe ON")
        print(self.source.inst.query(f":SENSe1:TOUTput:STATe?"))

        self.source.inst.write(f":TRIGger1:TRAN:TOUTput:STATe 1")
        print(self.source.inst.query(f":TRIGger1:TRAN:TOUTput:STATe?"))
        self.source.inst.write(f":TRIGger1:TRAN:TOUTput:SIGNal EXT1")
        print(self.source.inst.query(f":TRIGger1:TRAN:TOUTput:SIGNAL?"))

        self.source.inst.write(f":TRIGger1:ACQ:TOUTput:STATe 1")
        print(self.source.inst.query(f":TRIGger1:ACQ:TOUTput:STATe?"))
        self.source.inst.write(f":TRIGger1:ACQ:TOUTput:SIGNal EXT1")
        print(self.source.inst.query(f":TRIGger1:ACQ:TOUTput:SIGNAL?"))

        self.source.inst.write(f":ARM1:TRAN:LAYER:TOUT:STATE ON")
        print(self.source.inst.query(f":ARM1:TRAN:LAYER:TOUT:STATE?"))
        self.source.inst.write(f":ARM1:TRAN:LAYER:TOUT:SIGNAL EXT1")
        print(self.source.inst.query(f":ARM1:TRAN:LAYER:TOUT:SIGNAL?"))

        self.source.inst.write(f":ARM1:ACQ:LAYER:TOUT:STATE ON")
        print(self.source.inst.query(f":ARM1:ACQ:LAYER:TOUT:STATE?"))
        self.source.inst.write(f":ARM1:ACQ:LAYER:TOUT:SIGNAL EXT1")
        print(self.source.inst.query(f":ARM1:ACQ:LAYER:TOUT:SIGNAL?"))
        
        
        self.source.inst.query("*OPC?")
        mylogger.info(f"({self.name}) SETUP SOURCE TOUT")

        self.multi1.inst.write(f"SENSe:VOLTage:DC:APERture {.001}")
        self.multi1.inst.write(f"SAMP:COUN {100}")
        self.multi1.inst.write(f"TRIG:COUN 1")
        self.multi1.inst.write(f"TRIG:DEL 0")
        self.multi1.inst.write(f"TRIG:SOUR BUS")
        self.multi1.inst.query(f"*OPC?")
        self.multi1.inst.write("INIT")
        mylogger.info(f"({self.name}) SETUP MULTI1")


        self.multi2.inst.write(f"SENSe:VOLTage:DC:APERture {.001}")
        self.multi2.inst.write(f"SAMP:COUN {150}")
        self.multi2.inst.write(f"TRIG:COUN 1")
        self.multi2.inst.write(f"TRIG:DEL 0")
        self.multi2.inst.write(f"TRIG:SOUR BUS")
        self.multi2.inst.query(f"*OPC?")
        self.multi2.inst.write("INIT")
        mylogger.info(f"({self.name}) SETUP MULTI2")


    def setup(
        self, source_frequency=1, source_offset=0, points_per_chunk=100, amplitude=1, chunks=1
    ):
        sleep(1)
        channels = [1, 2]
        for channel in channels:
            self.source.inst.query("*OPC?")
            self.source.inst.write(f":SOURce{channel}:FUNC:MODE VOLT")
            self.source.inst.write(f":SOURce{channel}:VOLTage:MODE ARB")
            self.source.inst.write(f":SOURce{channel}:ARB:COUNt {chunks}")
            self.source.inst.write(f":SOURce{channel}:ARB:FUNCtion:SHAPe SIN")
            self.source.inst.query("*OPC?")

            self.source.inst.write(f":SOURce{channel}:ARB:VOLTage:SINusoid:AMPLitude {amplitude}")
            self.source.inst.write(
                f":SOURce{channel}:ARB:VOLTage:SINusoid:FREQuency {source_frequency}"
            )
            self.source.inst.write(f":SOURce{channel}:ARB:VOLTage:SINusoid:OFFSet {source_offset}")
            self.source.inst.query("*OPC?")

            self.source.inst.write(f":TRIGger{channel}:TRAN:COUNt 1")
            self.source.inst.write(f":TRIGger{channel}:TRAN:SOURce AINT")
            self.source.inst.query("*OPC?")

            self.source.inst.write(f":OUTPut{channel}:ON:AUTO ON")
            self.source.inst.query("*OPC?")
        self.source.inst.write(f":SOURce{2}:ARB:VOLTage:SINusoid:AMPLitude {-amplitude}")
        mylogger.info(f"({self.name}) SETUP SOURCE SIN")


        for channel in channels:
            self.source.inst.write(f':SENSe{channel}:FUNCtion:ON "VOLT"')
            self.source.inst.write(
                f":SENS{channel}:VOLTage:DC:APER {1/points_per_chunk/source_frequency}"
            )
            #self.source.inst.write(f":SENS{channel}:VOLTage:DC:PROT 0.1")
            self.source.inst.query("*OPC?")
            self.source.inst.write(f":TRIGger{channel}:ACQuire:COUNt {chunks*points_per_chunk}")
            self.source.inst.write(f":TRIGger{channel}:ACQuire:SOURce:SIGNal TIM")
            self.source.inst.write(f":TRIGger{channel}:ACQuire:TIMer {1/points_per_chunk}")
            self.source.inst.query("*OPC?")
        mylogger.info(f"({self.name}) SETUP SOURCE ACQ")

        self.source.inst.write(f":SOURc:TOUTput:SIGNal EXT5")
        self.source.inst.write(f":SOURc:DIGital:EXTernal:TOUTput:TYPE EDGE")
        self.source.inst.write(f":SOURc:DIGital:EXTernal:TOUTput:EDGE:POSition BEFore")
        self.source.inst.write(f":SOURc:DIGital:EXTernal:TOUTput:EDGE:WIDTh 0.01")
        self.source.inst.write(f":TRIGger:TRAN:TOUTput:STATe ON")
        self.source.inst.write(f":TRIGger:TRAN:TOUTput:SIGNal EXT5")

        mylogger.info(f"({self.name}) SETUP SOURCE TOUT")

        for multi in [self.multi1]:
            self.inst = multi.inst
            self.inst.write(f"SENSe:VOLTage:DC:APERture {.0095}")
            multi.get_errorstatus()
            self.inst.write(f"SAMP:COUN {100}")
            # self.inst.write(f"SAMP:COUN:PRETrigger {int(chunks*points_per_chunk*.1)}")
            multi.get_errorstatus()

            self.inst.write(f"TRIG:COUN 1")
            multi.get_errorstatus()
            self.inst.write(f"TRIG:DEL 0")
            # self.inst.write(f"SAMP:TIM {1/points_per_chunk/source_frequency}")
            multi.get_errorstatus()
            self.inst.query(f"*OPC?")
            multi.get_errorstatus()
            self.inst.write(f"TRIG:SOUR EXT")
            multi.get_errorstatus()
            self.inst.write(f"TRIGger:SLOPe POSitive")
            multi.get_errorstatus()
            self.inst.query(f"*OPC?")
            multi.get_errorstatus()
            self.inst.write(f"INIT")
            multi.get_errorstatus()
        mylogger.info(f"({self.name}) SETUP SAMPLE ACQ")

    def get(self):
        import numpy as np
        import matplotlib.pyplot as plt
        #self.multi2.inst.write(f"*TRG")
        #self.multi1.inst.write(f"*TRG")
        #self.source.trigger_all()
        self.source.inst.write(f"INIT (@1,2)")

        sleep(1)

        dings = str(self.source.inst.query(":FETCh:ARRay:VOLTage? (@1,2)"))
        print(dings)
        chunk1, chunk2 =0,0
        check=True
        while check:
            try:
                self.multi1.get_errorstatus()
                chunk1 = np.fromstring(self.multi1.inst.query("READ?"), sep=',')
                #chunk2 = np.fromstring(self.multi2.inst.query("READ?"), sep=',')
                check=False
            except:
                sleep(.1)



        dings = np.fromstring(dings, sep=",")

        dings1 = dings[::2]
        dings2 = dings[1::2]
        mylogger.info(f"({self.name}) {dings1} {dings2}")

        plt.figure(1)
        plt.plot(dings1,'.')
        plt.plot(dings2,'.')
        plt.plot(chunk1,'.')
        plt.plot(chunk2,'.')

        plt.show()

"""


"""


            
            
            
    def setup(
        self, source_frequency=1, source_offset=0, points_per_chunk=100, amplitude=1, chunks=1
    ):
        sleep(1)
        channels = [1, 2]
        for channel in channels:
            self.source.inst.query("*OPC?")
            self.source.inst.write(f":SOURce{channel}:FUNC:MODE VOLT")
            self.source.inst.write(f":SOURce{channel}:VOLTage:MODE ARB")
            self.source.inst.write(f":SOURce{channel}:ARB:COUNt {chunks}")
            self.source.inst.write(f":SOURce{channel}:ARB:FUNCtion:SHAPe SIN")
            self.source.inst.query("*OPC?")

            self.source.inst.write(f":SOURce{channel}:ARB:VOLTage:SINusoid:AMPLitude {amplitude}")
            self.source.inst.write(
                f":SOURce{channel}:ARB:VOLTage:SINusoid:FREQuency {source_frequency}"
            )
            self.source.inst.write(f":SOURce{channel}:ARB:VOLTage:SINusoid:OFFSet {source_offset}")
            self.source.inst.query("*OPC?")

            self.source.inst.write(f":TRIGger{channel}:ARM:COUNt 1")
            self.source.inst.write(f":TRIGger{channel}:ARM:SOURce AINT")
            self.source.inst.query("*OPC?")

            self.source.inst.write(f":OUTPut{channel}:ON:AUTO ON")
            self.source.inst.query("*OPC?")
        self.source.inst.write(f":SOURce{2}:ARB:VOLTage:SINusoid:AMPLitude {-amplitude}")
        mylogger.info(f"({self.name}) SETUP SOURCE SIN")

        for channel in channels:
            self.source.inst.write(f':SENSe{channel}:FUNCtion:ON "VOLT"')
            self.source.inst.write(
                f":SENS{channel}:VOLTage:DC:APER {points_per_chunk/source_frequency}"
            )
            #self.source.inst.write(f":SENS{channel}:VOLTage:DC:PROT 0.1")
            self.source.inst.query("*OPC?")
            self.source.inst.write(f":TRIGger{channel}:ACQuire:COUNt {chunks*points_per_chunk}")
            self.source.inst.write(f":TRIGger{channel}:ACQuire:SOURce:SIGNal TIMer")
            self.source.inst.write(f":TRIGger{channel}:ACQuire:TIMer {1/points_per_chunk}")
            self.source.inst.query("*OPC?")
        mylogger.info(f"({self.name}) SETUP SOURCE ACQ")

        for multi in [self.multi1, self.multi2]:
            self.inst=multi.inst
            self.inst.write(f"SENSe:VOLTage:DC:APERture {.95/points_per_chunk/source_frequency}")
            self.inst.write(f"SAMP:COUN {points_per_chunk*chunks}")
            #self.inst.write(f"SAMP:COUN:PRETrigger {int(chunks*points_per_chunk*.1)}")
            multi.get_errorstatus()

            self.inst.write(f"TRIG:COUN 1")
            self.inst.write(f"TRIG:DEL 0")
            #self.inst.write(f"SAMP:TIM {1/points_per_chunk/source_frequency}")
            multi.get_errorstatus()
            self.inst.query(f"*OPC?")
            self.inst.write(f"TRIG:SOUR TIM")
            self.inst.write(f"TRIG:SLOPe POSitive")
            self.inst.query(f"*OPC?")
            self.inst.write(f"INIT")
        mylogger.info(f"({self.name}) SETUP SAMPLE ACQ")


    def get(self):
        self.source.trigger_all()
        self.multi2.inst.write(f"*TRG")
        self.multi1.inst.write(f"*TRG")


        chunk1 = 0
        chunk2 = 0
        check=True
        while check:
            try:
                dings = str(self.source.inst.query(":FETCh:ARRay:VOLTage? (@1,2)"))
                chunk1 = self.multi1.get_chunk()
                chunk2 = self.multi2.get_chunk()
                check=False
            except:
                sleep(.1)
                mylogger.info(f"({self.name}) Retrieving failed.")


        import numpy as np
        import matplotlib.pyplot as plt

        dings = np.fromstring(dings, sep=",")

        dings1 = dings[::2]
        dings2 = dings[1::2]

        plt.figure(1)
        plt.plot(dings1)
        plt.plot(dings2)
        plt.plot(chunk1)
        plt.plot(chunk2)

        plt.show()
"""
