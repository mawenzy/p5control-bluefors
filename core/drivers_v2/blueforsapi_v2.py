# Import needed libraries
import requests
import numpy as np
from time import time
from logging import getLogger
from threading import Thread, Event
from queue import Queue
from time import sleep

# https://stackoverflow.com/questions/33046733/force-requests-to-use-ipv4-ipv6
# ahhhhhhhhh!
requests.packages.urllib3.util.connection.HAS_IPV6 = False

from p5control.drivers.basedriver import BaseDriver
from p5control import DataGateway, InstrumentGateway

"""path in the hdf5 file in /status/BlueFors"""
T_STRING = '/temperature'
P_STRING = '/pressure'
H_STRING = '/heater'
VC_STRING = P_STRING
D_STRING = '/driver'

# Logger
logger = getLogger(__name__)

class BlueForsWorker(Thread):
    def __init__(
        self,
        name,
        url,
        delay=1/13.7,
    ):
        logger.info('%s.__init__()', name)
        super().__init__()

        self._name = name
        self.url = url
        self.delay = delay
        self.data = {"data": {}}

        self.exit_request = Event()
        self.queue = Queue()

        self._latest_t_measurement = 0

    def run(self):
        logger.info('%s is running.', self._name)
        while not self.exit_request.is_set():
            req = requests.get(
                    self.url,
                    timeout=3,
                )
            self.data = req.json()

            if 'driver.lakeshore.status.inputs.channelA.temperature' in self.data['data'].keys():
                data = self.data['data']['driver.lakeshore.status.inputs.channelA.temperature']['content']['latest_value']
                date, value = float(data['date'])/1000.0, data['value']
                if date!=self._latest_t_measurement and value!='outdated':
                    self._latest_t_measurement = date
                    try:
                        value = float(value)
                    except ValueError:
                        value = np.nan
                    self.queue.put(np.array([date, value]))
            sleep(self.delay)
        logger.info('%s stopped.', self._name)
class BlueForsAPI(BaseDriver):
    def __init__(self, name, address='localhost:49099'):
        logger.info('%s.__init__()', name)
        self._name = name
        self._address = address

        self.url = f"http://{self._address}/values/"
        
        self.blueforsworker = BlueForsWorker(
            name=f"{self._name}Worker", 
            url= self.url,
            )
        self.blueforsworker.start()
 
        # Sample Heater Default Settings
        self.sample_heater_pid_mode = False
        self.sample_heater_manual_mode = False
        self.sample_heater_mode = 5              # 0 off, 2 manual, 3 zone, 5 pid
        self.sample_heater_input = 17            # 17 control input, 1-16 channel 1-16
        self.sample_heater_enable_at_start = 1   # 0 off, 1 on (default)
        self.sample_heater_filtering = 0         # 0 off, 1 on (default)
        self.sample_heater_autoscan_delay = 10   # setpoint change pause / autoscan delay [s]: 10 (default)
        self.sample_heater_polarity = 0          # 0 unipolar, 1 bipolar (default)
        self.sample_heater_range = 3             # 0-8: off, 31.6µA, 100µA, 316 µA, 1mA, 3.16mA, 10mA, 31.6mA, 100mA (default:3)
                                                 # 1-7 equals 1.2e-7 till 1.2e-0 W
        self.sample_heater_resistance = 120.0    # Heater Resistance [Ohm]: 120.0 
        self.sample_heater_display_units = 2     # 1 current, 2 power (default)
        self.sample_heater_manual_value = 0      # manual value [W]: 0.0
        self.sample_heater_p = 10.0              # P-Value: 10.0
        self.sample_heater_i = 20.0              # I-Value: 20.0
        self.sample_heater_d =  0.0              # D-Value:  0.0
        self.sample_heater_setpoint = .1         # Setpoint [K]: 0.1       
        self.sample_heater_enable_ramping = 0    # 0 off, 1 on (default)
        self.sample_heater_ramping_rate = 1      # Ramping Rate [K/min]: 1 (default)
        self.possible_ranges = ['1.2e-7', '1.2e-6', '1.2e-5', '1.2e-4', '1.2e-3', '1.2e-2', '1.2e-1', '1.2e-0']
        
        self.status_keys = [
            ['A-sample', 'driver.lakeshore.status.inputs.channelA.temperature', 0, T_STRING],
            ['1-50K',    'driver.lakeshore.status.inputs.channel1.temperature', 0, T_STRING],
            ['2-4K',     'driver.lakeshore.status.inputs.channel2.temperature', 0, T_STRING],
            ['3-magnet', 'driver.lakeshore.status.inputs.channel3.temperature', 0, T_STRING],
            ['5-still',  'driver.lakeshore.status.inputs.channel5.temperature', 0, T_STRING],
            ['6-mxc',    'driver.lakeshore.status.inputs.channel6.temperature', 0, T_STRING],
            ['7-fmr',    'driver.lakeshore.status.inputs.channel7.temperature', 0, T_STRING],
            ['8-mcbj',   'driver.lakeshore.status.inputs.channel8.temperature', 0, T_STRING],
            ['P1',       'driver.maxigauge.pressures.p1',                       0, P_STRING],
            ['P2',       'driver.maxigauge.pressures.p2',                       0, P_STRING],
            ['P3',       'driver.maxigauge.pressures.p3',                       0, P_STRING],
            ['P4',       'driver.maxigauge.pressures.p4',                       0, P_STRING],
            ['P5',       'driver.maxigauge.pressures.p5',                       0, P_STRING],
            ['P6',       'driver.maxigauge.pressures.p6',                       0, P_STRING],
            ['Flow',     'driver.vc.flow',                                      0, VC_STRING],
            ['output_power',    'driver.lakeshore.status.outputs.sample.measured',           0, H_STRING],
            ['mode',            'driver.lakeshore.settings.outputs.sample.mode',             0, H_STRING],
            ['input',           'driver.lakeshore.settings.outputs.sample.input',            0, H_STRING],
            ['enable_at_start', 'driver.lakeshore.settings.outputs.sample.enabled_at_start', 0, H_STRING],
            ['filtering',       'driver.lakeshore.settings.outputs.sample.filtering',        0, H_STRING],
            ['autoscan_delay',  'driver.lakeshore.settings.outputs.sample.autoscan_delay',   0, H_STRING],
            ['polarity',        'driver.lakeshore.settings.outputs.sample.polarity',         0, H_STRING],
            ['range',           'driver.lakeshore.settings.outputs.sample.range',            0, H_STRING],
            ['resistance',      'driver.lakeshore.settings.outputs.sample.resistance',       0, H_STRING],
            ['display_units',   'driver.lakeshore.settings.outputs.sample.display_units',    0, H_STRING],
            ['manual_value',    'driver.lakeshore.settings.outputs.sample.manual_value',     0, H_STRING],
            ['p',               'driver.lakeshore.settings.outputs.sample.p',                0, H_STRING],
            ['i',               'driver.lakeshore.settings.outputs.sample.i',                0, H_STRING],
            ['d',               'driver.lakeshore.settings.outputs.sample.d',                0, H_STRING],
            ['setpoint',        'driver.lakeshore.settings.outputs.sample.setpoint',         0, H_STRING],
            ['enable_ramping',  'driver.lakeshore.settings.outputs.sample.enable_ramping',   0, H_STRING],
            ['ramping_rate',    'driver.lakeshore.settings.outputs.sample.ramping_rate',     0, H_STRING],
        ]


    def close(self):
        logger.info('%s.close()', self._name)

        while not self.blueforsworker.exit_request.is_set():
            self.blueforsworker.exit_request.set()
            sleep(.1)

    """
    Measurement
    """
    def start_measuring(self):
        logger.info(f'{self._name}.start_measuring()')
        size = self.blueforsworker.queue.qsize()
        for i in range(size):
            res = self.blueforsworker.queue.get()

    def get_data(self):
        logger.info(f'{self._name}.get_data()')
        size = self.blueforsworker.queue.qsize()
        date, value = [], []
        for i in range(size):
            res = self.blueforsworker.queue.get()
            date.append(res[0])
            value.append(res[1])
        if date:
            return {
                "time": date,
                "Tsample": value,
            }

    """
    Status measurement
    """
    def get_status(self):
        logger.info('%s.get_status()', self._name)
        
        pid_mode = self.sample_heater_pid_mode
        manual_mode = self.sample_heater_manual_mode
        xor_mode = pid_mode ^ manual_mode

        ranges = self.sample_heater_range * int(xor_mode)
        manual_value = float(self.sample_heater_manual_value * int(manual_mode))
        if xor_mode:
            if pid_mode:
                self.sample_heater_mode = 5
            if manual_mode:
                self.sample_heater_mode = 2
        else:
            self.sample_heater_mode = 0

        # post settings
        post = {
            "data": {
                "driver.lakeshore.settings.outputs.sample.mode": {"content": {"value": self.sample_heater_mode}},
                "driver.lakeshore.settings.outputs.sample.input": {"content": {"value": self.sample_heater_input}},
                "driver.lakeshore.settings.outputs.sample.enabled_at_start": {"content": {"value": self.sample_heater_enable_at_start}},
                "driver.lakeshore.settings.outputs.sample.filtering": {"content": {"value": self.sample_heater_filtering}},
                "driver.lakeshore.settings.outputs.sample.autoscan_delay": {"content": {"value": self.sample_heater_autoscan_delay}},
                "driver.lakeshore.settings.outputs.sample.polarity": {"content": {"value": self.sample_heater_polarity}},
                "driver.lakeshore.settings.outputs.sample.range": {"content": {"value": ranges}},
                "driver.lakeshore.settings.outputs.sample.resistance": {"content": {"value": self.sample_heater_resistance}},
                "driver.lakeshore.settings.outputs.sample.display_units": {"content": {"value": self.sample_heater_display_units}},
                "driver.lakeshore.settings.outputs.sample.manual_value": {"content": {"value": manual_value}},
                "driver.lakeshore.settings.outputs.sample.p": {"content": {"value": float(self.sample_heater_p)}},
                "driver.lakeshore.settings.outputs.sample.i": {"content": {"value": float(self.sample_heater_i)}},
                "driver.lakeshore.settings.outputs.sample.d": {"content": {"value": float(self.sample_heater_d)}},
                "driver.lakeshore.settings.outputs.sample.setpoint": {"content": {"value": self.sample_heater_setpoint}},
                "driver.lakeshore.settings.outputs.sample.enable_ramping": {"content": {"value": self.sample_heater_enable_ramping}},
                "driver.lakeshore.settings.outputs.sample.ramping_rate": {"content": {"value": self.sample_heater_ramping_rate}},
                "driver.lakeshore.write": {"content": {"call": 1}},
                }
            }
        _ = requests.post(self.url, json=post, timeout=1)

        # get data
        data = self.blueforsworker.data
        now = time()

        # get heater settings
        status = {
            "driver": {
                "time": now,
                "pid_mode": self.sample_heater_pid_mode,
                "manual_mode": self.sample_heater_manual_mode,
                "mode": self.sample_heater_mode,
                "input": self.sample_heater_input,
                "enable_at_start": self.sample_heater_enable_at_start,
                "filtering": self.sample_heater_filtering,
                "autoscan_delay": self.sample_heater_autoscan_delay,
                "polarity": self.sample_heater_polarity,
                "range": self.sample_heater_range,
                "resistance": self.sample_heater_resistance,
                "display_units": self.sample_heater_display_units,
                "manual_value": self.sample_heater_manual_value,
                "p": self.sample_heater_p,
                "i": self.sample_heater_i,
                "d": self.sample_heater_d,
                "setpoint": self.sample_heater_setpoint,
                "enable_ramping": self.sample_heater_enable_ramping,
                "ramping_rate": self.sample_heater_ramping_rate,
            },
            "status":{},
        }

        # get actual temperatures, pressures, flow and heater values
        for i, d in enumerate(self.status_keys):
            status_key = d[0]
            ls_key = d[1]
            latest_time = d[2]
            if ls_key in data['data'].keys():
                temp = data['data'][ls_key]['content']['latest_value']
                date, value = temp['date']/1000.0, temp['value']
                if date != latest_time and value != 'outdated':
                    self.status_keys[i][2] = date
                    try:
                        value = float(value)
                    except ValueError:
                        value = np.nan
                    status['status'][status_key] = {'time': [date], 'T': [value]}
        return status

    """
    Save Status
    """
    def _save_status(
        self,
        hdf5_path: str,
        status,
        dgw
    ):
        logger.info('%s._save_status()', self._name)

        # Save Driver Settings
        dgw.append(f"{hdf5_path}{D_STRING}", status["driver"])

        # Save Status
        for i,d in enumerate(self.status_keys):
            status_key = d[0]
            string = d[3]
            temp = status['status']
            if status_key in temp:
                dgw.append(
                    f"{hdf5_path}{string}/{status_key}", 
                    temp[status_key]
                    )

    """
    set Heater Values
    """

    def setPIDMode(self, pid:bool):
        logger.info('%s.setPIDMode()', self._name)
        self.sample_heater_pid_mode = pid
    def getPIDMode(self):
        logger.info(f'{self._name}.getPIDMode()')
        return self.sample_heater_pid_mode
    
    def setManualMode(self, manual:bool):
        logger.info('%s.setManualMode()', self._name)
        self.sample_heater_manual_mode = manual
    def getManualMode(self):
        logger.info(f'{self._name}.getManualMode()')
        return self.sample_heater_manual_mode
    
    def setManualValue(self, manual_value:float):
        logger.info('%s.setManualValue()', self._name)
        self.sample_heater_manual_value = manual_value
    def getManualValue(self):
        logger.info(f'{self._name}.getManualValue()')
        return self.sample_heater_manual_value

    def setSetPoint(self, setpoint:float):
        logger.info('%s.setSetPoint()', self._name)
        self.sample_heater_setpoint = setpoint
    def getSetPoint(self):
        logger.info('%s.getSetPoint()', self._name)
        return self.sample_heater_setpoint
    
    def setRange(self, range:int):
        logger.info('%s.setRange()', self._name)
        self.sample_heater_range = range
    def getRange(self):
        logger.info('%s.getRange()', self._name)
        return self.sample_heater_range
    
    def setP(self, P:float):
        logger.info('%s.setP()', self._name)
        self.sample_heater_p = P
    def getP(self):
        logger.info('%s.getP()', self._name)
        return self.sample_heater_p
    
    def setI(self, I:float):
        logger.info('%s.setI()', self._name)
        self.sample_heater_i = I
    def getI(self):
        logger.info('%s.getI()', self._name)
        return self.sample_heater_i
    
    def setD(self, D:float):
        logger.info('%s.setD()', self._name)
        self.sample_heater_d = D
    def getD(self):
        logger.info('%s.getD()', self._name)
        return self.sample_heater_d

