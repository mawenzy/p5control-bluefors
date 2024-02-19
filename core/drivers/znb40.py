import logging
import time
import pyvisa

import numpy as np

from p5control.drivers.basedriver import BaseDriver, ThreadSafeBaseDriver
from p5control import DataGateway, InstrumentGateway


logger = logging.getLogger(__name__)

class ZNB40(ThreadSafeBaseDriver):
    def __init__(self, 
                 name,              
                 address='192.168.1.104', 
                 case = 'time',
                 S = '11',
                 res: float = 0.1):
        
        self._name = name
        self._address = address
        self.refresh_delay = 1

        if case != 'time':
            if case != 'frequency':
                raise KeyError(
                    "%s: case must be either 'time' or 'frequency'",
                      self._name
                      )
        
        self.case = case
        self.S = S
        self.input_channel = int(S[0])
        self.output_channel = int(S[1])
        
        self.output = 0
        self.power = 0.0
        self.points = 0
        self.bandwith = 0.0

        # t sweep       
        self.tsweep_frequency = 0.0
        self.tsweep_measuring = 0

        # f sweep
        self._temp_avg = 1
        self.fsweep_start = 0.0
        self.fsweep_stop = 0.0
        self.fsweep_average = 0

        self.open()
        self.initialize()

    def open(self):
        logger.debug('%s.open()', self._name)
        # Open Connection
        rm = pyvisa.ResourceManager()
        self._inst = rm.open_resource(f'TCPIP0::{self._address}::inst0::INSTR')  
        self._inst.timeout=1e5 
        self._inst.read_termination = '\n'

    def query(self, request):
        output = self._inst.query(request)
        # print(output)
        return output
    def write(self, writing):
        self._inst.write(writing)
    def read(self):
        output = self._inst.read()
        # print(output)
        return output
        
    # for important messages, lol
    def message(self, message="DON'T TOUCH\nRemote test running..."):
        logger.debug('%s.message()', self._name)
        self.write(f'SYST:USER:DISP:TITL "{message}"')

    def initialize(self):
        # reset the device
        self.write('*RST')
        # delete all old traces
        self.write('CALC:PAR:DEL:ALL')
        # turn continous measurement off
        self.write(f'INITiate1:CONTinuous OFF')
        self.write(f'INITiate2:CONTinuous OFF')
        # turn Display to remote control
        self.write('SYSTem:TSLock SCReen')
        # close soft tool menu
        self.write('SYSTem:DISPlay:BAR:STOols OFF')
        # Displaying the data increases measurement time 
        self.write('SYSTem:DISPlay:UPDate OFF')
        # Turn off Output
        self.setOutput(False)
        # Turn on one Display
        self.write("DISP:WIND:STAT ON")
        # Setting right Sweep Type
        match self.case:
            case 'time':
                self.write(f"SENSe{self.output_channel}:SWEep:Type POINt")
            case 'frequency':
                self.write(f"SENSe{self.output_channel}:SWEep:Type LINear")
        # Setting right Scattering Parameter
        self.write(f"CALC{self.output_channel}:PAR:SDEF 'Tr1', 'S{self.input_channel}{self.output_channel}'")
        # Activate Trace
        self.write(f"DISPlay:WINDow:TRAC1:FEED 'Tr1'")
        # Update display once
        self.write('SYSTem:DISPlay:UPDate ONCE')
        # self.message()

    def close(self):
        logger.debug('%s.close()', self._name)
        # Turn to Local
        self.write('@LOC')
        # Turn of Key Lock
        self.write('SYSTem:KLOCk OFF')
        # turn Display to local control
        self.write('SYSTem:TSLock OFF)')
        # reset the device
        self.write('*RST')
        # Go to local control
        self.write('SYSTem:DISPlay:UPDate ON')
        # enable toolbar
        self.write('SYSTem:DISPlay:BAR:STOols ON') 
        # Turn off Output
        self.setOutput(False)
        # Close Connection       
        self._inst.close()

    """
    Setup Measurement
    """
    def setup_fsweep_timeout(self):
        logger.debug('%s.setup_fsweep_timeout()', self._name)
        # sets timeout time between measurments to zero
        self.write(f"SENSe{self.output_channel}:SWEep:TIME:AUTO ON")
        
        # gets maximum timeout time, to prevent errors during long time meas.
        time=float(self.query(f'SENSe{self.output_channel}:SWEep:TIME?'))
        if self._temp_avg > 1:
            self._inst.timeout=int((time*self._temp_avg*2.5+10)*1000)
        else:
            self._inst.timeout=int((time*2.5+10)*1000)

    def setup_tsweep_timeout(self):
        logger.debug('%s.setup_tsweep_timeout()', self._name)
        self._inst.timeout = 30000
        # self._inst.timeout=int(np.ceil(np.max([measure_time*1.2,10])*1e3))

    def setup_tsweep_settings(self):
        logger.debug('%s.setup_tsweep_settings()', self._name)

        # TODO understand!!!
        ### Sensor Stuff
        ### 
        measure_time=2     # [s]
        sampling_rate=400  # [Hz]
        
        points=int(np.ceil(measure_time*sampling_rate))
        bandwidths=[  1, 1.5,  2,  3,  5,  7, 10,
                        1e1,15e0,2e1,3e1,5e1,7e1,1e2,
                        1e2,15e1,2e2,3e2,5e2,7e2,1e3,
                        1e3,15e2,2e3,3e3,5e3,7e3,1e4,
                        1e4,15e3,2e4,3e4,5e4,7e4,1e5,
                        1e5,15e4,2e5,3e5,5e5,7e5,1e6]
        check=False
        bandwidth = 0
        for bw in bandwidths:
                if check==False:
                        self.write("SENSe2:BANDwidth %i"%int(bw))
                        self.write("SENSe2:SWEep:POINts %i"%points)
                        self.write("SENSe2:SWEep:TIME %f"%measure_time)
                        self.write('*WAI')
                        checktime=float(self.query('SENSe2:SWEep:TIME?'))
                        if checktime==measure_time:
                                check=True
                                bandwidth=bw
        if check==True:
                self.write("SENSe2:BANDwidth %i"%bandwidth)
                self.write("SENSe2:SWEep:POINts %i"%points)
                self.write("SENSe2:SWEep:TIME %f"%measure_time)
                # inst.write('*WAI')
                # inst.write('SYSTem:DISPlay:UPDate OFF')
                dwelltime=float(self.query('SENSe2:SWEep:DWELl?'))
        else: 
                logger.error('ERROR: Sampling Rate is too HIGH!')
                dwelltime=np.NaN
        
    def setup_measuring(self):
        match self.case:
            case 'time':
                self.setup_tsweep_timeout()
                # self.setup_tsweep_settings()
            case 'frequency':
                self.setup_fsweep_timeout()

    """
    Retrieve Data
    """

    def retrieve_data(self):
        # gets S parameter
        sdata = self.query(f"CALC{self.output_channel}:DATA:TRACe? 'Tr1', SDAT")
        data = np.fromstring(sdata, dtype='float64',sep=',')
        real, imag = data[::2], data[1::2]
        S = np.array(real+1j*imag, dtype='complex128')
        S_dB = 20*np.log10(np.abs(S))
        return S_dB, real, imag

    def get_data(self):
        logger.debug(f'{self._name}.get_data()')
        data = None
        if self.output:
            # initialize measurement
            self.write(f"INIT{self.output_channel}")
            self.write('*WAI')
            timestamp = time.time()

            match self.case:
                case 'time':
                    if self.tsweep_measuring:
                        S_dB, real, imag = self.retrieve_data()

                        timeaxis = self.query(f'CALC{self.output_channel}:DATA:STIM?')
                        timeaxis = np.fromstring(timeaxis, dtype='float64', sep=',')
                        checktime= float(self.query(f'SENSe{self.output_channel}:SWEep:TIME?'))
                        timeaxis = (timeaxis-1)/np.shape(timeaxis)*checktime + timestamp

                        data = {
                            "time": list(timeaxis),
                            "S_dB": list(S_dB),
                        }

                case 'frequency':                    
                    S_dB, real, imag = self.retrieve_data()
                
                    data = {
                            'time': timestamp,
                            'S_dB': S_dB,
                            'Re': real,
                            'Im': imag,
                            }
        
            # shows measured data once. (is better for performance)
            self.write('SYSTem:DISPlay:UPDate ONCE')
            self.write('SYSTem:DISPlay:BAR:STOols OFF')
            self.write(f"DISP:TRAC1:Y:AUTO ONCE")
        return data
    
    
    def _save_data(
        self,
        hdf5_path: str,
        data,
        dgw: DataGateway,
    ):
        """Save data to hdf5 through a gateway
        
        Parameters
        ----------
        hdf5_path : str
            base hdf5_path under which you should save the data
        array
            data to save
        dgw : DataGateway
            gateway to the dataserver
        """
        if data is None:
            return
        match self.case:
            case 'time':
                path = f"{hdf5_path}/{self._name}"
                dgw.append(path, data)
            case 'frequency':
                path = f"{hdf5_path}/{self._name}"
                try:
                    dgw.append(path, 
                                data, 
                                x_axis = 'f [Hz]',
                                start = self.fsweep_start,
                                stop = self.fsweep_stop,
                                points = self.points,
                                plot_config = "lnspc")
                except ValueError:
                    raise Warning('Mismatch in data shape! Make new measurement, when changing points!' )
    
    """
    Status
    """
    def get_status(self):
        status = {}
        now = time.time()
        output = self.output
        power = self.power
        points = self.points
        bandwidth = self.bandwith
        status = {
                "time": now,
                "output": output,
                "power": power,
                "points": points,
                "bandwidth": bandwidth,
            }
        match self.case:
            case 'time':
                status["frequency"] = self.tsweep_frequency
                status["measuring"] = self.tsweep_measuring
            case 'frequency':
                status['start'] = self.fsweep_start
                status['stop'] = self.fsweep_stop
                status['average'] = self.fsweep_average
        return status

    """
    Common Properties
    """
    def setOutput(self, output):
        logger.debug('%s.setOutput()', self._name)
        self.write(f'OUTput{self.output_channel}:STATe {int(output)}')
        self.getOutput()

    def getOutput(self):
        logger.debug('%s.getOutput()', self._name)
        output = bool(int(self.query(f'OUTput{self.output_channel}:STATe?')))
        self.output = output
        return output

    def setPower(self, value):
        logger.debug('%s.setPower()', self._name)
        self.write(f"SOURce{self.output_channel}:POWer {value} dBm")
        self.getPower()

    def getPower(self):
        logger.debug('%s.getPower()', self._name)
        power = float(self.query(f"SOURce{self.output_channel}:POWer?"))
        self.power = power
        return power
        
    def setPoints(self, value):
        logger.debug('%s.setPoints()', self._name)
        self.write(f"SENSe{self.output_channel}:SWEep:POINts {int(value)}")
        self.getPoints()

    def getPoints(self):
        logger.debug('%s.getPoints()', self._name)
        points = int(self.query(f"SENSe{self.output_channel}:SWEep:POINts?"))
        self.points = points
        return points

    def setBandwidth(self, value):
        logger.debug('%s.setBandwidth()', self._name)
        """
        possible values:   1, 1.5,  2,  3,  5,  7, 10,
                         1e1,15e0,2e1,3e1,5e1,7e1,1e2,
                         1e2,15e1,2e2,3e2,5e2,7e2,1e3,
                         1e3,15e2,2e3,3e3,5e3,7e3,1e4,
                         1e4,15e3,2e4,3e4,5e4,7e4,1e5,
                         1e5,15e4,2e5,3e5,5e5,7e5,1e6
        """
        self.write(f"SENSe{self.input_channel}:BANDwidth {value}")
        self.getBandwidth()

    def getBandwidth(self):
        logger.debug('%s.getBandwidth()', self._name)
        bandwidth = float(self.query(f"SENSe{self.input_channel}:BANDwidth?"))
        self.bandwith = bandwidth
        return bandwidth
    
    """
    Properties t-sweep
    """

    def setTSweepFrequency(self, frequency):
        logger.debug('%s.setTSweepFrequency()', self._name)
        self.write(f'SOUR{self.output_channel}:FREQ:FIX {frequency}')
        self.getTSweepFrequency()

    def getTSweepFrequency(self):
        logger.debug('%s.getTSweepFrequency()', self._name)
        frequency = float(self.query(f'SOUR{self.output_channel}:FREQ:FIX?'))
        self.tsweep_frequency = frequency
        return frequency  
    
    def setTSweepMeasuring(self, value):
        logger.debug('%s.setTSweepMeasuring()', self._name)
        self.tsweep_measuring = value

    def getTSweepMeasuring(self):
        logger.debug('%s.getTSweepMeasuring()', self._name)
        return self.tsweep_measuring

    """
    Properties f-sweep
    """
    
    def setFSweepStart(self, value):
        logger.debug('%s.setFSweepStart()', self._name)
        self.write(f"SENSe{self.output_channel}:FREQuency:STARt {value} Hz")
        self.getFSweepStart()
    
    def getFSweepStart(self):
        logger.debug('%s.getFSweepStart()', self._name)
        start = float(self.query(f"SENSe{self.output_channel}:FREQuency:STARt?"))
        self.fsweep_start = start
        return start
    
    def setFSweepStop(self, value):
        logger.debug('%s.setFSweepStop()', self._name)
        self.write(f"SENSe{self.output_channel}:FREQuency:STOP {value} Hz")
        self.getFSweepStop()

    def getFSweepStop(self):
        logger.debug('%s.getFSweepStop()', self._name)
        stop = float(self.query(f"SENSe{self.output_channel}:FREQuency:STOP?"))
        self.fsweep_stop = stop
        return stop
    
    def setFSweepAverage(self, value:int):
        logger.debug('%s.setFSweepAverage()', self._name)
        if value > 1:
            self.write(f"SENSe{self.input_channel}:AVERage:COUNt {value}")
            self.write(f"SENSe{self.input_channel}:AVERage:STATe ON")
            self.write(f"SENSe{self.input_channel}:AVERage:CLEar")
            self.write(f"SENSe{self.input_channel}:SWEep:COUNt {value}")
        else:
            self.write(f"SENSe{self.input_channel}:AVERage:STATe OFF")
        self._temp_avg = value
        self.getFSweepAverage()

    def getFSweepAverage(self):
        logger.debug('%s.getFSweepAverage()', self._name)
        if self._temp_avg <=1:
            return_value = 1
        else:
            return_value = int(self.query(f"SENSe{self.input_channel}:AVERage:COUNt?"))
        self.fsweep_average = return_value
        return return_value


    # self.setup_fsweep_settings()
    # def setup_fsweep_settings(self):
    #     logger.debug('%s.setup_fsweep_settings()', self._name) 
    #     self.setFSweepRunning(False)
    #     self.setFSweepStart(1e9)
    #     self.setFSweepStop(40e9)
    #     self.setFSweepPoints(391)
    #     self.setFSweepPower(-30)
    #     self.setFSweepBandwidth(1e6)
        # self.setFSweepAverage(0)



    # def setup_measurement(self):
    #     self.write("SENSe2:SWEep:Type POINt")

    #     ### Sensor Stuff

    #     self._inst.timeout = 30000
    #     # self._inst.timeout=int(np.ceil(np.max([measure_time*1.2,10])*1e3))

    #     self.write("CALC2:PAR:SDEF 'Tr1', 'S22'")
    #     self.write("DISPlay:WINDow:TRAC2:FEED 'Tr1'")

    #     ### 
    #     measure_time=2     # [s]
    #     sampling_rate=400  # [Hz]
        
    #     points=int(np.ceil(measure_time*sampling_rate))
    #     bandwidths=[  1, 1.5,  2,  3,  5,  7, 10,
    #                     1e1,15e0,2e1,3e1,5e1,7e1,1e2,
    #                     1e2,15e1,2e2,3e2,5e2,7e2,1e3,
    #                     1e3,15e2,2e3,3e3,5e3,7e3,1e4,
    #                     1e4,15e3,2e4,3e4,5e4,7e4,1e5,
    #                     1e5,15e4,2e5,3e5,5e5,7e5,1e6]
    #     check=False
    #     for bw in bandwidths:
    #             if check==False:
    #                     self.write("SENSe2:BANDwidth %i"%int(bw))
    #                     self.write("SENSe2:SWEep:POINts %i"%points)
    #                     self.write("SENSe2:SWEep:TIME %f"%measure_time)
    #                     self.write('*WAI')
    #                     checktime=float(self.query('SENSe2:SWEep:TIME?'))
    #                     if checktime==measure_time:
    #                             check=True
    #                             bandwidth=bw
    #     if check==True:
    #             self.write("SENSe2:BANDwidth %i"%bandwidth)
    #             self.write("SENSe2:SWEep:POINts %i"%points)
    #             self.write("SENSe2:SWEep:TIME %f"%measure_time)
    #             # inst.write('*WAI')
    #             # inst.write('SYSTem:DISPlay:UPDate OFF')
    #             dwelltime=float(self.query('SENSe2:SWEep:DWELl?'))
    #     else: 
    #             logger.error('ERROR: Sampling Rate is too HIGH!')
    #             dwelltime=np.NaN

    # def start_measurement(self):
    #      pass

    # def get_data(self):
    #     self.write(f"INITiate{self.channel}")
    #     self.write('*WAI')
    #     timeaxis = self.query('CALC2:DATA:STIM?')
    #     timeaxis = np.fromstring(timeaxis, dtype='float64', sep=',')
    #     checktime=float(self.query('SENSe2:SWEep:TIME?'))
    #     timeaxis = (timeaxis-1)/np.shape(timeaxis)*checktime

    #     # gets S21 parameter and save them as real and imag
    #     query_str = "CALC2:DATA:TRACe? 'Tr1', SDAT"
    #     sdata = self.query(query_str)
    #     data = np.fromstring(sdata, dtype='float64',sep=',')
    #     real, imag = data[::2], data[1::2]
         

    
