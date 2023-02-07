import serial
import numpy as np
import os
from time import sleep
from datetime import datetime
"""
author: Oliver Irtenkauf
date: 21.01.2021

TODO:
- datetime format einheitlich. check for easy read function.
- check for filt: off
- check fer seri setting

Usage of GIR2002, with EBW3 adapter, thermo couple Type K
TC an Pin 10 und 11, Kabel: grün/weiß -> TypK, more @ evaporater cabinett
setup rear side + button2:
InP: t.tc
SEns: NiCr-Ni (type K) [-70..-.1..250°C, -200..1..850°C]
rES: 0.1
Unit: °C
FiLt: 0.01

(Explanation: this digital filter is a digital replica of a low pass filter.
Note: If the digital filter is “off” the internal mains hum suppression of the GIR2002 is deactivated. This adjustment is ideal for fastest response to even small changes of the signal, but the display and the analog output gets more turbulent. Therefore the filter should set to at least 0.01 for „ordi-nary‟ application A filter value of at least 0.1 is recommended for the input type S.)

rear side + button1:
outP: no

manuals:
GIR2002_e.pdf
GMH3xxx_interface_without_DLL.pdf

Example:
from drivers.thermo import GIR2002
thermo=GIR2002('COM11')
thermo.logging(path='thermo_data',
               name='_pos_is_free_hanging',
               avg=100,
               sleeper=0,
               show_progress=True)
# thermo.close()
"""

class GIR2002(serial.Serial):
    def __init__(self, com_port='COM11'):
        '''
        initialize black serial magix
        '''
        serial.Serial.__init__(self, com_port)
        self.baudrate = 4800
        self.bytesize = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.timeout = 1
        self.xonxoff = False
        self.rts = False
        self.dtr = True
        self.inter_byte_timeout = None
        self.reset_input_buffer()
        self.reset_output_buffer()
        self.breaker=False
        
        
    def value(self):
        '''
        get Thermodata: Black fu**ing Magic.
        try 'GMH3xxx - Serial Interface' 
        aka GMH3xxx_interface_without_DLL.pdf
        bugs as hell with decimal point. just ignore,
        because. \pm 0.1°C is as good as it gets, with Type K
        '''
        try:
            self.write(bytearray((254,0,61))) #255 - address 1, command 0, crc 61
            response=bytes(self.read(6))
            integer=(256*(255-response[3])+response[4])&16383-2048
            value=integer/10
    #         spez={'49152':1000, '32768':100, '16384':10, '0':1}
    #         decimal_point='%i'%((256*255-response[3])&49152)
    #         value=integer/spez[decimal_point]
    #         print(value, end='\r')
        except:
            value=np.nan
        return value

    def show_value(self):
        '''
        simple live Progress
        '''
        i=0
        while True:
            i=(i+1)%4
            progress='\\-/|<v>^'
            T=self.value()
            if self.breaker==True:
                break
            if T is not np.nan:
                print('%s T = %2.1f °C  '%(progress[i],T), end='\r')
            else:
                print('%s lost signal  '%progress[i], end='\r')
    
    def average_value(self, avg=1, sleeper=1):
        '''
        simple average method to decrease data pilage
        '''
        if avg>1:
            T=0
            for i in range(avg):
                sleep(sleeper)
                T=T+self.value()
            T=T/avg
        elif avg==1 or avg==0:
            sleep(sleeper)
            T=self.value()
        else:
            print('U dumb?')
            T=np.Nan
        return T
    
    def logging(self,
                path='thermo_data',
                name='',
                avg=100,
                sleeper=0,
                show_progress=True):
        '''
        simple temperature logging.
        file structure, like BlueFors T logging
        day,time,T [°C]
        '''
        if not os.path.exists(path):
            os.makedirs(path)
        name='GIR2002_log%s_%s.csv'%(name,
             str(str(datetime.now())).replace(':','-')[:-7])
        i=0
        progress='\\-/|<v>^'
        while True:
            if self.breaker==True:
                break
            try:
                T=self.average_value(avg=avg, sleeper=sleeper)
                if show_progress is True:
                    i=(i+1)%4
                    if T is not np.nan:
                        print('%s T = %2.3f °C  '%(progress[i],T), end='\r')
                    else:
                        print('%s u lost signal  '%progress[i], end='\r')
                if T is not np.nan:
                    now=datetime.now()
                    now=now.strftime('%d-%m-%y,%H:%M:%S')
                    with open('%s/%s'%(path,name),'a') as fd:
                        fd.write('%s,%f\n'%(now,T))
            except:
                print('no signal')