# Import needed libraries
import time, requests
import numpy as np
from logging import getLogger

# https://stackoverflow.com/questions/33046733/force-requests-to-use-ipv4-ipv6
# ahhhhhhhhh!
requests.packages.urllib3.util.connection.HAS_IPV6 = False

from p5control.drivers.basedriver import BaseDriver
from p5control import DataGateway, InstrumentGateway

T_STRING = '/temperature'
P_STRING = '/pressure'
H_STRING = '/heater'
VC_STRING = ''
"""path in the hdf5 file in /status/BlueFors"""

# Logger
logger = getLogger(__name__)

class BlueForsAPI(BaseDriver):
    def __init__(self, name, address='localhost:49099'):
        logger.debug('%s._handle_target_temperature()', name)
        self._name = name
        self._address = address
        self.refresh_delay = 1/13.7 /2

        self.url = f"http://{self._address}/values/"

        # Memory
        self._latest_t_measurement = 0

        self._latest_T50K = 0
        self._latest_T4K = 0
        self._latest_Tmagnet = 0
        self._latest_Tstill = 0
        self._latest_Tmxc = 0
        self._latest_Tfmr = 0
        self._latest_Tmcbj = 0
        self._latest_Tsample = 0
        
        self._latest_P1 = 0
        self._latest_P2 = 0
        self._latest_P3 = 0
        self._latest_P4 = 0
        self._latest_P5 = 0
        self._latest_P6 = 0

        self._latest_Flow = 0

    """
    Measurement
    """
    def get_data(self):
        logger.debug(f'{self._name}.get_data()')
        req = requests.get(
                    self.url,
                    timeout=3,
                )
        data = req.json()
        if 'driver.lakeshore.status.inputs.channelA.temperature' in data['data'].keys():
            data = data['data']['driver.lakeshore.status.inputs.channelA.temperature']['content']['latest_value']
            date, value = float(data['date'])/1000.0, data['value']
            if date!=self._latest_t_measurement and value!='outdated':
                self._latest_t_measurement = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                return {
                    "time": date,
                    "Tsample": value,
                }

    """
    set heater values
    """

    def setSampleHeater(self, heating:bool):
        logger.debug('%s.setSampleHeater()', self._name)
        json = {
            "data": {
                "driver.lakeshore.settings.outputs.sample.enable_ramping": {"content": {"value": int(heating)}},
                "driver.lakeshore.write": {"content": {"call": 1}},
                }
            }
        requests.post(self.url, json=json)

    def getSampleHeater(self):
        req = requests.get(
                    self.url,
                    timeout=3,
                )
        data = req.json()
        key = 'driver.lakeshore.settings.outputs.sample.enable_ramping'
        if key in data['data'].keys():
            dat = data['data'][key]['content']['latest_value']
            try:
                output = bool(int(dat['value']))
            except ValueError:
                output = None
        return output


    def setTargetSampleTemperature(self, setpoint:float):
        logger.debug('%s.setTargetSampleTemperature()', self._name)
        json = {
            "data": {
                "driver.lakeshore.settings.outputs.sample.setpoint": {"content": {"value": setpoint}},
                "driver.lakeshore.write": {"content": {"call": 1}},
                }
            }
        requests.post(self.url, json=json)

    def getTargetSampleTemperature(self):
        req = requests.get(
                    self.url,
                    timeout=3,
                )
        data = req.json()
        key = 'driver.lakeshore.settings.outputs.sample.setpoint'
        if key in data['data'].keys():
            dat = data['data'][key]['content']['latest_value']
            try:
                T = float(dat['value'])
            except ValueError:
                T = np.nan
        return T

    """
    Status measurement
    """
    def get_status(self):
        logger.debug('%s.get_status()', self._name)
        req = requests.get(
                    self.url,
                    timeout=3,
                )
        data = req.json()
        now = time.time()
        status = {}

        # Thermometer
        # 50K Thermometer
        key = 'driver.lakeshore.status.inputs.channelA.temperature'
        if key in data['data'].keys():
            T50K = data['data'][key]['content']['latest_value']
            date, value = T50K['date']/1000.0, T50K['value']
            if date!=self._latest_T50K and value!='outdated':
                self._latest_T50K = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['T50K'] = {'time': [date], 'T': [value]}

        # 4K Thermometer
        key = 'driver.lakeshore.status.inputs.channel2.temperature'
        if key in data['data'].keys():
            T4K = data['data'][key]['content']['latest_value']
            date, value = T4K['date']/1000.0, T4K['value']
            if date!=self._latest_T4K and value!='outdated':
                self._latest_T4K = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['T4K'] = {'time': [date], 'T': [(value)]}
            
        # Magnet Thermometer
        key = 'driver.lakeshore.status.inputs.channel3.temperature'
        if key in data['data'].keys():
            Tmagnet = data['data'][key]['content']['latest_value']
            date, value = Tmagnet['date']/1000.0, Tmagnet['value']
            if date!=self._latest_Tmagnet and value!='outdated':
                self._latest_Tmagnet = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['Tmagnet'] = {'time': [date], 'T': [(value)]}

        # Still Thermometer
        key = 'driver.lakeshore.status.inputs.channel5.temperature'
        if key in data['data'].keys():
            Tstill = data['data'][key]['content']['latest_value']
            date, value = Tstill['date']/1000.0, Tstill['value']
            if date!=self._latest_Tstill and value!='outdated':
                self._latest_Tstill = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['Tstill'] = {'time': [date], 'T': [(value)]}
            
        # MXC Thermometer
        key = 'driver.lakeshore.status.inputs.channel6.temperature'
        if key in data['data'].keys():
            Tmxc = data['data'][key]['content']['latest_value']
            date, value = Tmxc['date']/1000.0, Tmxc['value']
            if date!=self._latest_Tmxc and value!='outdated':
                self._latest_Tmxc = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['Tmxc'] = {'time': [date], 'T': [(value)]}
            
        # FMR Thermometer
        key = 'driver.lakeshore.status.inputs.channel7.temperature'
        if key in data['data'].keys():
            Tfmr = data['data'][key]['content']['latest_value']
            date, value = Tfmr['date']/1000.0, Tfmr['value']
            if date!=self._latest_Tfmr and value!='outdated':
                self._latest_Tfmr = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['Tfmr'] = {'time': [date], 'T': [(value)]}
            
        # MCBJ Thermometer
        key = 'driver.lakeshore.status.inputs.channel8.temperature'
        if key in data['data'].keys():
            Tmcbj = data['data'][key]['content']['latest_value']
            date, value = Tmcbj['date']/1000.0, Tmcbj['value']
            if date!=self._latest_Tmcbj and value!='outdated':
                self._latest_Tmcbj = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['Tmcbj'] = {'time': [date], 'T': [(value)]}
            
        # Sample Thermometer
        key = 'driver.lakeshore.status.inputs.channelA.temperature'
        if key in data['data'].keys():
            Tsample = data['data'][key]['content']['latest_value']
            date, value = Tsample['date']/1000.0, Tsample['value']
            if date!=self._latest_Tsample and value!='outdated':
                self._latest_Tsample = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['Tsample'] = {'time': [date], 'T': [(value)]}

        ## Heater
        # sample Heater on / off
        key = 'driver.lakeshore.settings.outputs.sample.enable_ramping'
        if key in data['data'].keys():
            dat = data['data'][key]['content']['latest_value']
            try:
                output = bool(int(dat['value']))
            except ValueError:
                output = np.nan
            status['sampleheater'] = {'time': [now], 'output': [output]}

        # sample setpoint
        key = 'driver.lakeshore.settings.outputs.sample.setpoint'
        if key in data['data'].keys():
            dat = data['data'][key]['content']['latest_value']
            try:
                T = float(dat['value'])
            except ValueError:
                T = np.nan
            status['Tsampleheater'] = {'time': [now], 'T': [T]}

        ## Pressures
        # P1
        key = 'driver.maxigauge.pressures.p1'
        if key in data['data'].keys():
            P1 = data['data'][key]['content']['latest_value']
            date, value = P1['date']/1000.0, P1['value']
            if date!=self._latest_P1 and value!='outdated' and value!='':
                self._latest_P1 = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['P1'] = {'time': [date], 'T': [(value)]}
            
        # P2
        key = 'driver.maxigauge.pressures.p2'
        if key in data['data'].keys():
            P2 = data['data'][key]['content']['latest_value']
            date, value = P2['date']/1000.0, P2['value']
            if date!=self._latest_P2 and value!='outdated' and value!='':
                self._latest_P2 = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['P2'] = {'time': [date], 'T': [(value)]}
            
        # P3
        key = 'driver.maxigauge.pressures.p3'
        if key in data['data'].keys():
            P3 = data['data'][key]['content']['latest_value']
            date, value = P3['date']/1000.0, P3['value']
            if date!=self._latest_P3 and value!='outdated' and value!='':
                self._latest_P3 = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['P3'] = {'time': [date], 'T': [(value)]}
            
        # P4
        key = 'driver.maxigauge.pressures.p4'
        if key in data['data'].keys():
            P4 = data['data'][key]['content']['latest_value']
            date, value = P4['date']/1000.0, P4['value']
            if date!=self._latest_P4 and value!='outdated' and value!='':
                self._latest_P4 = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['P4'] = {'time': [date], 'T': [(value)]}
            
        # P5
        key = 'driver.maxigauge.pressures.p5'
        if key in data['data'].keys():
            P5 = data['data'][key]['content']['latest_value']
            date, value = P5['date']/1000.0, P5['value']
            if date!=self._latest_P5 and value!='outdated' and value!='':
                self._latest_P5 = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['P5'] = {'time': [date], 'T': [(value)]}
            
        # P6
        key = 'driver.maxigauge.pressures.p6'
        if key in data['data'].keys():
            P6 = data['data'][key]['content']['latest_value']
            date, value = P6['date']/1000.0, P6['value']
            if date!=self._latest_P6 and value!='outdated' and value!='':
                self._latest_P6 = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['P6'] = {'time': [date], 'T': [(value)]}
        
        ## Valve Control
        # Flow
        key = 'driver.vc.flow'
        if key in data['data'].keys():
            Flow = data['data'][key]['content']['latest_value']
            date, value = Flow['date']/1000.0, Flow['value']
            if date!=self._latest_Flow:
                self._latest_Flow = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['Flow'] = {'time': [date], 'T': [(value)]}

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
        logger.debug('%s._save_status()', self._name)
        if 'T50K' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/1-50K", status['T50K'])
        if 'T4K' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/2-4K", status['T4K'])
        if 'Tmagnet' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/3-magnet", status['Tmagnet'])
        if 'Tstill' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/5-still", status['Tstill'])
        if 'Tmxc' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/6-mxc", status['Tmxc'])
        if 'Tfmr' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/7-fmr", status['Tfmr'])
        if 'Tmcbj' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/8-mcbj", status['Tmcbj'])
        if 'Tsample' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/A-sample", status['Tsample'])

        if 'sampleheater' in status:
            dgw.append(f"{hdf5_path}{H_STRING}/sampleheater", status['sampleheater'])
        if 'Tsampleheater' in status:
            dgw.append(f"{hdf5_path}{H_STRING}/Tsampleheater", status['Tsampleheater'])
            
        if 'P1' in status:
            dgw.append(f"{hdf5_path}{P_STRING}/p1", status['P1'])
        if 'P2' in status:
            dgw.append(f"{hdf5_path}{P_STRING}/p2", status['P2'])
        if 'P3' in status:
            dgw.append(f"{hdf5_path}{P_STRING}/p3", status['P3'])
        if 'P4' in status:
            dgw.append(f"{hdf5_path}{P_STRING}/p4", status['P4'])
        if 'P5' in status:
            dgw.append(f"{hdf5_path}{P_STRING}/p5", status['P5'])
        if 'P6' in status:
            dgw.append(f"{hdf5_path}{P_STRING}/p6", status['P6'])

        if 'Flow' in status:
            dgw.append(f"{hdf5_path}{VC_STRING}/flow", status['Flow'])
