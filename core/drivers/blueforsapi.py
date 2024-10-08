# Import needed libraries
import json
from requests import get as requests_get
import numpy as np
from logging import getLogger

from p5control.drivers.basedriver import BaseDriver
from p5control import DataGateway, InstrumentGateway

T_STRING = '/temperature'
P_STRING = '/pressure'
VC_STRING = ''
"""path in the hdf5 file in /status/BlueFors"""

# Logger
logger = getLogger(__name__)

class BlueForsAPI(BaseDriver):
    def __init__(self, name, address='localhost:49099'):
        self._name = name
        self._address = address
        self.refresh_delay = 1/13.7

        # Memory
        self._latest_T50K = 0
        self._latest_T4K = 0
        self._latest_Tmagnet = 0
        self._latest_Tstill = 0
        self._latest_Tmxc = 0
        self._latest_Tfmr = 0
        self._latest_Tmcbj = 0

        self._latest_Tauto = -1
        self._latest_Tchannel = 0
        
        self._latest_P1 = 0
        self._latest_P2 = 0
        self._latest_P3 = 0
        self._latest_P4 = 0
        self._latest_P5 = 0
        self._latest_P6 = 0

        self._latest_Flow = 0
        
    """
    Measurement
    % TODO
    def get_data(self):
        logger.debug(f'{self._name}.get_data()')

        return {
            "time":
            "Tmcbj":
        }
    """

    """
    Response
    """
    def get_response(self):
        req = requests_get(
                    f"http://{self._address}/values",
                    timeout=3,
                )
        logger.debug(f'{self._name}.get_response()')
        return req.json()

    """
    Status measurement
    """
    def get_status(self):
        data = self.get_response()
        status = {}

        # Thermometer
        # 50K Thermometer
        T50K = data['data']['driver.lakeshore.status.inputs.channel1.temperature']['content']['latest_value']
        date, value = T50K['date']/1000.0, T50K['value']
        if date!=self._latest_T50K and value!='outdated':
            self._latest_T50K = date
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            status['T50K'] = {'time': [date], 'T': [value]}

        # 4K Thermometer
        T4K = data['data']['driver.lakeshore.status.inputs.channel2.temperature']['content']['latest_value']
        date, value = T4K['date']/1000.0, T4K['value']
        if date!=self._latest_T4K and value!='outdated':
            self._latest_T4K = date
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            status['T4K'] = {'time': [date], 'T': [(value)]}
            
        # Magnet Thermometer
        Tmagnet = data['data']['driver.lakeshore.status.inputs.channel3.temperature']['content']['latest_value']
        date, value = Tmagnet['date']/1000.0, Tmagnet['value']
        if date!=self._latest_Tmagnet and value!='outdated':
            self._latest_Tmagnet = date
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            status['Tmagnet'] = {'time': [date], 'T': [(value)]}

        # Still Thermometer
        Tstill = data['data']['driver.lakeshore.status.inputs.channel5.temperature']['content']['latest_value']
        date, value = Tstill['date']/1000.0, Tstill['value']
        if date!=self._latest_Tstill and value!='outdated':
            self._latest_Tstill = date
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            status['Tstill'] = {'time': [date], 'T': [(value)]}
            
        # MXC Thermometer
        Tmxc = data['data']['driver.lakeshore.status.inputs.channel6.temperature']['content']['latest_value']
        date, value = Tmxc['date']/1000.0, Tmxc['value']
        if date!=self._latest_Tmxc and value!='outdated':
            self._latest_Tmxc = date
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            status['Tmxc'] = {'time': [date], 'T': [(value)]}
            
        # FMR Thermometer
        Tfmr = data['data']['driver.lakeshore.status.inputs.channel7.temperature']['content']['latest_value']
        date, value = Tfmr['date']/1000.0, Tfmr['value']
        if date!=self._latest_Tfmr and value!='outdated':
            self._latest_Tfmr = date
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            status['Tfmr'] = {'time': [date], 'T': [(value)]}
            
        # MCBJ Thermometer
        Tmcbj = data['data']['driver.lakeshore.status.inputs.channel8.temperature']['content']['latest_value']
        date, value = Tmcbj['date']/1000.0, Tmcbj['value']
        if date!=self._latest_Tmcbj and value!='outdated':
            self._latest_Tmcbj = date
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            status['Tmcbj'] = {'time': [date], 'T': [(value)]}

        # Thermometers/Others
        # Thermometer Autoscan
        Tauto = data['data']['driver.lakeshore.status.scanner.autoscan']['content']['latest_value']
        value = Tauto['value']
        if value != self._latest_Tauto and value!='outdated':
            self._latest_Tauto = value
            try:
                value = int(value)
            except ValueError:
                value = -1
            status['Tauto'] = {'time': [Tauto['date']/1000.0], 'T': [(value)]}
            
        # Thermometer Channel
        Tchannel = data['data']['driver.lakeshore.status.scanner.channel']['content']['latest_value']
        date, value = Tchannel['date']/1000.0, Tchannel['value']
        if date!=self._latest_Tchannel and value!='outdated':
            self._latest_Tchannel = date
            try:
                value = int(value)
            except ValueError:
                value = -1
            status['Tchannel'] = {'time': [date], 'T': [(value)]}

        # Pressures
        # P1
        P1 = data['data']['driver.maxigauge.pressures.p1']['content']['latest_value']
        date, value = P1['date']/1000.0, P1['value']
        if date!=self._latest_P1 and value!='outdated' and value!='':
            self._latest_P1 = date
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            status['P1'] = {'time': [date], 'T': [(value)]}
            
        # P2
        P2 = data['data']['driver.maxigauge.pressures.p2']['content']['latest_value']
        date, value = P2['date']/1000.0, P2['value']
        if date!=self._latest_P2 and value!='outdated' and value!='':
            self._latest_P2 = date
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            status['P2'] = {'time': [date], 'T': [(value)]}
            
        # P3
        P3 = data['data']['driver.maxigauge.pressures.p3']['content']['latest_value']
        date, value = P3['date']/1000.0, P3['value']
        if date!=self._latest_P3 and value!='outdated' and value!='':
            self._latest_P3 = date
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            status['P3'] = {'time': [date], 'T': [(value)]}
            
        # P4
        P4 = data['data']['driver.maxigauge.pressures.p4']['content']['latest_value']
        date, value = P4['date']/1000.0, P4['value']
        if date!=self._latest_P4 and value!='outdated' and value!='':
            self._latest_P4 = date
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            status['P4'] = {'time': [date], 'T': [(value)]}
            
        # P5
        P5 = data['data']['driver.maxigauge.pressures.p5']['content']['latest_value']
        date, value = P5['date']/1000.0, P5['value']
        if date!=self._latest_P5 and value!='outdated' and value!='':
            self._latest_P5 = date
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            status['P5'] = {'time': [date], 'T': [(value)]}
            
        # P6
        P6 = data['data']['driver.maxigauge.pressures.p6']['content']['latest_value']
        date, value = P6['date']/1000.0, P6['value']
        if date!=self._latest_P6 and value!='outdated' and value!='':
            self._latest_P6 = date
            try:
                value = float(value)
            except ValueError:
                value = np.nan
            status['P6'] = {'time': [date], 'T': [(value)]}
        
        # Valve Control
        # Flow
        try:
            # catches the case VC is not connected
            Flow = data['data']['driver.vc.flow']['content']['latest_value']
            date, value = Flow['date']/1000.0, Flow['value']
            if date!=self._latest_Flow:
                self._latest_Flow = date
                try:
                    value = float(value)
                except ValueError:
                    value = np.nan
                status['Flow'] = {'time': [date], 'T': [(value)]}
        except:
            pass

        logger.debug(f'{self._name}.get_status()')
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
        if 'T50K' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/50K", status['T50K'])
        if 'T4K' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/4K", status['T4K'])
        if 'Tmagnet' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/Magnet", status['Tmagnet'])
        if 'Tstill' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/Still", status['Tstill'])
        if 'Tmxc' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/MXC", status['Tmxc'])
        if 'Tfmr' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/FMR", status['Tfmr'])
        if 'Tmcbj' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/MCBJ", status['Tmcbj'])

        if 'Tauto' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/other/AutoScan", status['Tauto'])
        if 'Tchannel' in status:
            dgw.append(f"{hdf5_path}{T_STRING}/other/Channel", status['Tchannel'])
            
        if 'P1' in status:
            dgw.append(f"{hdf5_path}{P_STRING}/P1", status['P1'])
        if 'P2' in status:
            dgw.append(f"{hdf5_path}{P_STRING}/P2", status['P2'])
        if 'P3' in status:
            dgw.append(f"{hdf5_path}{P_STRING}/P3", status['P3'])
        if 'P4' in status:
            dgw.append(f"{hdf5_path}{P_STRING}/P4", status['P4'])
        if 'P5' in status:
            dgw.append(f"{hdf5_path}{P_STRING}/P5", status['P5'])
        if 'P6' in status:
            dgw.append(f"{hdf5_path}{P_STRING}/P6", status['P6'])

        if 'Flow' in status:
            dgw.append(f"{hdf5_path}{VC_STRING}/Flow", status['Flow'])
