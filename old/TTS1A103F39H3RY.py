from driver.KeysightAgilent34461A import KeysightAgilent34461A
from numpy import log, array
from logging import getLogger

# mylogger = getLogger(name=__name__)
mylogger = getLogger("driver")


class TTS1A103F39H3RY(KeysightAgilent34461A):
    def __init__(
        self,
        ip="192.168.1.109",
        name="Keysight Digital Thermometer",
    ):
        super(TTS1A103F39H3RY, self).__init__(ip=ip)

        self.name = name
        self.IDN = self.get_idn()
        self.set_resistance_config()

        self.r_twentyfive = 1e4
        self.one_over_t_twentyfive = 1 / 298.15
        self.beta = 3975.0
        mylogger.info(f"({self.name}) r25: {self.r_twentyfive}, beta: {self.beta}")

    def set_resistance_config(self, range="AUTO", resolution="MAX"):
        # MEASure:{RESistance|FRESistance}? [{<range>|AUTO|MIN|MAX|DEF}...
        # [, {<resolution>|MIN|MAX|DEF}]]
        self.inst.write(f"CONFigure:RESistance {range}, {resolution}")
        mylogger.info(f"({self.name}) Resistance range: {range}, resolution {resolution}")

    @property
    def temperature(self):
        """get resistance from device and calculate temperature.

        :return: temperature
        """
        resistance, utc_timer = self.get_reading()
        one_over_temperature = (
            log(float(resistance) / self.r_twentyfive) / self.beta + self.one_over_t_twentyfive
        )
        temperature = 1 / one_over_temperature - 273.15
        mylogger.info(f"({self.name}) Temperature: {temperature}")
        return temperature, utc_timer
