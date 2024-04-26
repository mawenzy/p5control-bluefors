"""
version v2:
- setAmplitude / getAmplitude
- fixed timeaxis

general notes:
 0-30 GHz: -30 to 10 dbm, typical up to 15 dbm
30-40 GHz: -30 to  8 dbm, typical up to 13 dbm

for power to amplitude:
power_dBm = 10*log10(P/P_0)
P_0 = 1 # mW
P_0 = .001 # W
P = V_rms**2/R # W
R = 50 # Ohm
V_rms = V / np.sqrt(2) # V

"""

import logging
import time
import pyvisa

import numpy as np

from p5control.drivers.basedriver import BaseDriver, ThreadSafeBaseDriver
from p5control import DataGateway, InstrumentGateway


logger = logging.getLogger(__name__)

# TODO everything

class ZNB40_source(ThreadSafeBaseDriver):
    def __init__(self, 
                 name,              
                 address='192.168.1.104', 
                 S = '11',
                 res: float = 0.1):
        logger.info('%s.__init__()', name)
        
        self._name = name
        self._address = address
        self.refresh_delay = .1

        self.S = S
        self.input_channel = int(S[0])
        self.output_channel = int(S[1])
        
        self.output = False
        self.frequency = 0.0
        self.amplitude = 0.01
        self.power = -30.0
  
        self.open()
        self.initialize()

        self.setOutput(self.output)
        self.setFrequency(self.frequency)
        self.setAmplitude(self.amplitude)

    def open(self):
        logger.info('%s.open()', self._name)
        rm = pyvisa.ResourceManager()
        self._inst = rm.open_resource(f'TCPIP0::{self._address}::inst0::INSTR')  
        self._inst.timeout=3e4 
        self._inst.read_termination = '\n'

    def query(self, request):
        output = self._inst.query(request)
        return output
    
    def write(self, command):
        self._inst.write(command)

    def read(self):
        output = self._inst.read()
        return output
        
    def message(self, message:str="DON'T TOUCH\nRemote test running..."):
        logger.info('%s.message()', self._name)
        self.write(f'SYST:USER:DISP:TITL "{message}"')
        # Write message on screen

    def initialize(self):
        logger.info('%s.initialize()', self._name)
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
        self.setOutput(self.output)
        # Turn on one Display
        self.write("DISP:WIND:STAT ON")
        # Setting right Sweep Type
        self.write(f"SENSe{self.output_channel}:SWEep:Type POINt")
        # Setting right Scattering Parameter
        self.write(f"CALC{self.output_channel}:PAR:SDEF 'Tr1', 'S{self.input_channel}{self.output_channel}'")
        # Activate Trace
        self.write(f"DISPlay:WINDow:TRAC1:FEED 'Tr1'")
        # Update display once
        self.write('SYSTem:DISPlay:UPDate ONCE')
        # self.message()

    def close(self):
        logger.info('%s.close()', self._name)
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
    Status
    """
    def get_status(self):
        logger.info('%s.get_status()', self._name)
        return {
                "output": self.output,
                "frequency": self.frequency,
                "amplitude": self.amplitude,
                "power": self.power,
            }

    """
    Common Properties
    """
    def setOutput(self, output):
        logger.info('%s.setOutput()', self._name)
        self.write(f'OUTput{self.output_channel}:STATe {int(output)}')
        self.getOutput()

    def getOutput(self):
        logger.info('%s.getOutput()', self._name)
        output = bool(int(self.query(f'OUTput{self.output_channel}:STATe?')))
        self.output = output
        return output

    def setFrequency(self, frequency):
        logger.info('%s.setFrequency()', self._name)
        self.write(f'SOUR{self.output_channel}:FREQ:FIX {frequency}')
        self.getFrequency()

    def getFrequency(self):
        logger.info('%s.getFrequency()', self._name)
        frequency = float(self.query(f'SOUR{self.output_channel}:FREQ:FIX?'))
        self.frequency = frequency
        return frequency  

    def setPower(self, value):
        logger.info('%s.setPower()', self._name)
        self.write(f"SOURce{self.output_channel}:POWer {value} dBm")
        self.getPower()

    def getPower(self):
        logger.info('%s.getPower()', self._name)
        power = float(self.query(f"SOURce{self.output_channel}:POWer?"))
        self.power = power
        self.amplitude = 10**(power/20-.5)
        return power
    
    def setAmplitude(self, amplitude):
        logger.info('%s.setAmplitude()', self._name)
        self.setPower(10*np.log10(amplitude**2*10))
        pass
    
    def getAmplitude(self):
        logger.info('%s.getAmplitude()', self._name)
        self.getPower()
        return self.amplitude

        
    

    
    """
    # Setup Measurement

def setup_tsweep_timeout(self):
        logger.debug('%s.setup_tsweep_timeout()', self._name)
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
        # self.setup_tsweep_settings()
    """

    
    """
    # Retrieve Data


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

            if self.measuring:
                S_dB, real, imag = self.retrieve_data()

                timeaxis = self.query(f'CALC{self.output_channel}:DATA:STIM?') # gibt nur einen linspace von 1 bis points #BULLSHIT
                timeaxis = np.fromstring(timeaxis, dtype='float64', sep=',')
                checktime= float(self.query(f'SENSe{self.output_channel}:SWEep:TIME?'))
                timeaxis = (timeaxis-1)/np.shape(timeaxis)*checktime + timestamp

                data = {
                    "time": list(timeaxis),
                    "S_dB": list(S_dB),
                    "S_real": list(real),
                    "S_imag": list(imag),
                }
        
            # shows measured data once. (is better for performance)
            self.write('SYSTem:DISPlay:UPDate ONCE')
            self.write('SYSTem:DISPlay:BAR:STOols OFF')
            self.write(f"DISP:TRAC1:Y:AUTO ONCE")
        return data

    """


    """
    # Measure Properties

    
    def setMeasuring(self, value):
        logger.debug('%s.setMeasuring()', self._name)
        self.measuring = value

    def getMeasuring(self):
        logger.debug('%s.getMeasuring()', self._name)
        return self.measuring

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
        '''
        possible values:   1, 1.5,  2,  3,  5,  7, 10,
                         1e1,15e0,2e1,3e1,5e1,7e1,1e2,
                         1e2,15e1,2e2,3e2,5e2,7e2,1e3,
                         1e3,15e2,2e3,3e3,5e3,7e3,1e4,
                         1e4,15e3,2e4,3e4,5e4,7e4,1e5,
                         1e5,15e4,2e5,3e5,5e5,7e5,1e6
        '''
        self.write(f"SENSe{self.input_channel}:BANDwidth {value}")
        self.getBandwidth()

    def getBandwidth(self):
        logger.debug('%s.getBandwidth()', self._name)
        bandwidth = float(self.query(f"SENSe{self.input_channel}:BANDwidth?"))
        self.bandwith = bandwidth
        return bandwidth
    """