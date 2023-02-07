# -*- coding: utf-8 -*-
"""
Created on Fri Jun 26 15:06:25 2020

Bugfix 09.12.2020
    # fsweep
    - sweep time -> timeout
    catch exception for high bandwidth and averaging

current Version 2.0 from 21.11.2020
Features:
    - use PyVISA protocoll
    # time mode
    - setup parameter and sampling rate
    - start measurement
    - pickup data
    - no printer so far
    # frequency sweep mode
    - reducing s_parameter sweep to S21 (due preamplifier)
    - saving complex and real part seperatly
    - saving temperature as well
    - reducing config file to essential
    - saving bfield with max number of digits
    - printer option
    - autoscaling at vna
    
@author: Oliver I.
Many Thanks to: Lukas Kammermeier und Lukas Siedentop

e.g.:
# measure time mode
from driver.vna2 import ZNB40
import time
vna=ZNB40(IP='192.168.1.104')
vna.enter()
config = vna.setup_time(measure_time=3.382,   # [s]
                        sampling_rate=400.58, # [Hz]
                        frequency=4e9,        # [Hz]
                        power=-10,            # [dBm]
                        saveconfig=True)
vna.measure_time()
t, Re, Im = vna.getdata_time(plotter=True)
vna.exit()

# Measure f_sweep
from vna2 import ZNB40
vna=ZNB40(IP='192.168.1.104')
vna.enter()
config=vna.setup_fsweep(start=2e6,
                     stop=4e10,
                     points=1e3,
                     bandwidth=1e3,
                     power=-10,
                     average=0,
                     printer=False,
                     saveconfig=True)
vna.measure_fsweep(sample_name='test',
                H=-99.9999,
                T=0,
                plotter=True,
                savefile=False,
                printer=False)
vna.exit()
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from datetime import datetime
import pyvisa

style='test'
plt.style.use('driver\%s.mplstyle'%style)

class ZNB40():
    
    #### general stuff
    
    def __init__(self, IP='192.168.1.104'):
        # black VISA magic
        # watch out for VISA and stuff
        # else dead
        rm=pyvisa.ResourceManager()
        inst=rm.open_resource('TCPIP0::'+IP+'::inst0::INSTR')
        #inst=rm.open_resource('TCPIP0::'+IP+'::hislip0')
        self.inst=inst
        self.inst.timeout=1e5
        
    def enter(self):
        # reset the device
        self.inst.write('*RST')
        # delete all old traces
        self.inst.write('CALC:PAR:DEL:ALL')
        # turn continous measurement off
        self.inst.write('INITiate1:CONTinuous OFF')
        # turn Display to remote control
        self.inst.write('SYSTem:TSLock SCReen')
        # close soft tool menu
        self.inst.write('SYSTem:DISPlay:BAR:STOols OFF')
        # displaying the data increases measurement time 
        self.inst.write('SYSTem:DISPlay:UPDate OFF')
        
        
        return self
    
    def exit(self):
        # unlock and turn on screen for local operation
        self.inst.write('SYSTem:TSLock OFF')
        self.inst.write('SYSTem:DISPlay:UPDate ON')
        self.inst.write('SYSTem:DISPlay:BAR:STOols ON')
        return self
    
    #### time mode
    
    def setup_time(self,
               measure_time=2,    # [s]
               sampling_rate=400, # [Hz]
               frequency=4e9,     # [Hz]
               power=-10,         # [dBm]
               saveconfig=True):
        
        # setup S21 scattering parameter
        self.inst.write("DISP:WIND:STAT ON")
        self.inst.write("CALC1:PAR:SDEF 'Tr1', 'S21'")
        self.inst.write("DISPlay:WINDow:TRAC1:FEED 'Tr1'")
        self.inst.timeout=int(np.ceil(np.max([measure_time*1.2,10])*1e3))
    
        # set sweep type to contant freqency over time
        self.inst.write("SENSe1:SWEep:Type POINt")
        self.inst.write("SENSe1:FREQuency:CENTer %i"%frequency)
        self.inst.write("SOURce1:POWer %i"%power)
        
        # set points by samplingrate and optimal bandwidth
        points=int(np.ceil(measure_time*sampling_rate))
        bandwidths=[  1, 1.5,  2,  3,  5,  7, 10,
                    1e1,15e0,2e1,3e1,5e1,7e1,1e2,
                    1e2,15e1,2e2,3e2,5e2,7e2,1e3,
                    1e3,15e2,2e3,3e3,5e3,7e3,1e4,
                    1e4,15e3,2e4,3e4,5e4,7e4,1e5,
                    1e5,15e4,2e5,3e5,5e5,7e5,1e6]
        check=False
        for bw in bandwidths:
            if check==False:
                self.inst.write("SENSe1:BANDwidth %i"%int(bw))
                self.inst.write("SENSe1:SWEep:POINts %i"%points)
                self.inst.write("SENSe1:SWEep:TIME %f"%measure_time)
                self.inst.write('*WAI')
                checktime=float(self.inst.query('SENSe1:SWEep:TIME?'))
                if checktime==measure_time:
                    check=True
                    bandwidth=bw
        if check==True:
            self.inst.write("SENSe1:BANDwidth %i"%bandwidth)
            self.inst.write("SENSe1:SWEep:POINts %i"%points)
            self.inst.write("SENSe1:SWEep:TIME %f"%measure_time)
            self.inst.write('*WAI')
            self.inst.write('SYSTem:DISPlay:UPDate OFF')
            dwelltime=float(self.inst.query('SENSe1:SWEep:DWELl?'))
        else: 
            print('ERROR: Sampling Rate is too HIGH!')
            dwelltime=np.NaN

        # builds config file
        date=str(datetime.now()) 
        config={'ZNB40':'time sweep',
                'timestamp_setup':date,
                's_param':'S21',
                'measure_time':measure_time,
                'sampling_rate':sampling_rate,
                'frequency':int(frequency),
                'power':power,
                'bandwidth':int(bandwidth),
                'points':points,
                'dwelltime':dwelltime}
            
        # Save Config File
        if saveconfig==True:  
            # append config file to current conig.json 
            with open('vna_time_config.json','a+') as f:
                json.dump(config,f,indent=1)
                
        return config
        
    def measure_time(self):
        # initialize measurement
        self.inst.write("INITiate")
        
    def getdata_time(self,plotter=True):
        # Wait for measurement to be finished
        self.inst.write('*WAI')
        self.inst.write('SYSTem:DISPlay:UPDate ONCE')
        
        # gets x-axis/time data and norm it
        timeaxis = self.inst.query('CALC1:DATA:STIM?')
        timeaxis = np.fromstring(timeaxis, dtype='float64', sep=',')
        checktime=float(self.inst.query('SENSe1:SWEep:TIME?'))
        timeaxis = (timeaxis-1)/np.shape(timeaxis)*checktime
        
        # gets S21 parameter and save them as real and imag
        query_str = "CALC1:DATA:TRACe? 'Tr1', SDAT"
        sdata = self.inst.query(query_str)
        data = np.fromstring(sdata, dtype='float64',sep=',')
        real, imag = data[::2], data[1::2]
        
        # plots plot to lookylook
        if plotter==True:
            plt.figure(1)
            bw=int(self.inst.query("SENSe1:BANDwidth?"))
            plt.plot(timeaxis,20*np.log(np.abs(real+imag*1j)),'.',
                    label='bandwidth: %i Hz'%bw)
            plt.grid()
            plt.title('Insertion loss of forward transmission')
            plt.ylabel('$20\cdot\ln|S_{21}|$ [dBm]')
            plt.xlabel('$t$ [s]')
            plt.legend(loc=1)
            
        return timeaxis, real, imag
    
    
    
    
    #### frequency sweep mode
    
    def setup_fsweep(self,
                     sample_name='no_sample_name_provided',
                     start=2e6,
                     stop=4e10,
                     points=1e3,
                     bandwidth=1e3,
                     power=-10,
                     average=0,
                     printer=False,
                     saveconfig=True
                     ):
        
        # setup S21 scattering parameter
        self.inst.write("DISP:WIND:STAT ON")
        self.inst.write("CALC1:PAR:SDEF 'Tr1', 'S21'")
        self.inst.write("DISPlay:WINDow:TRAC1:FEED 'Tr1'")
        
        # setup configuration
        self.inst.write("SENSe1:FREQuency:STARt %i Hz"%start)
        self.inst.write("SENSe1:FREQuency:STOP %i Hz"%stop)
        self.inst.write("SENSe1:SWEep:POINts %i"%points)
        self.inst.write("SENSe1:BANDwidth %i Hz"%bandwidth)
        self.inst.write("SOURce1:POWer %i dBm"%power)
        time=self.inst.query('SENSe1:SWEep:TIME?')
        
        # caring about averaging
        if average >1:
            self.inst.write("SENSe1:AVERage:COUNt %i"%average)
            self.inst.write("SENSe1:AVERage:STATe ON")
            self.inst.write("SENSe1:AVERage:CLEar")
            self.inst.write("SENSe1:SWEep:COUNt %i"%average)
        else:
            self.inst.write("SENSe1:AVERage:STATe OFF")
        
        # sets timeout time between measurments to zero
        self.inst.write("SENSe1:SWEep:TIME:AUTO ON")
        #self.inst.write('SYSTem:DISPlay:BAR:STOols OFF')
        #self.inst.write('SYSTem:DISPlay:UPDate ONCE')
        
        # gets maximum timeout time, to prevent errors during long time meas.
        time=float(self.inst.query('SENSe1:SWEep:TIME?'))
        if average >1:
            self.inst.timeout=int((time*average*2.5+10)*1000)
        else:
            self.inst.timeout=int((time*2.5+10)*1000)
            
        
        
        # print configuration parameter
        if printer==True:
            print('\nThe parameter are:')
            print('start frequency = %i Hz'%start)
            print('stop frequency = %i Hz'%stop)
            print('sweep points = %i'%points)
            print('bandwidth = %i Hz'%bandwidth)
            print('power = %i dBm'%power)
            print('\nThe cycle will need %.1f s.'%time)
              
        # builds config file
        date=str(datetime.now()) 
        config={'ZNB40':'frequency sweep',
                'sample_name':sample_name,
                'timestamp_setup':date,
                's_param':'S21',
                'start':int(start),
                'stop':int(stop),
                'points':int(points),
                'bandwidth':int(bandwidth),
                'power':power,
                'average':average,
                'sweeptime':time}
            
        # Save Config File
        if saveconfig==True:  
            # append config file to current conig.json 
            with open('vna_fsweep_config.json','a+') as f:
                json.dump(config,f,indent=1)
        
            if printer==True:
                print('\nSaved configuration successfully!')
        return config

    def measure_fsweep(self,
                config={'sample_name':'no_config_delivered'},
                H=-99.9999,
                T=0,
                plotter=False,
                savefile=True,
                printer=False
               ):        
        
        # initialize measurement
        self.inst.write("INITiate")
        self.inst.write('*WAI')
        
        # gets x-axis/frequency data
        # freq = self.inst.query('CALC1:DATA:STIM?')
        # freq=np.fromstring(freq, dtype='float64', sep=',')
        freq=np.linspace(config['start'],config['stop'],config['points'])
        
        # gets S21 parameter and save them as real and imag
        query_str = "CALC1:DATA:TRACe? 'Tr1', SDAT"
        sdata = self.inst.query(query_str)
        data = np.fromstring(sdata, dtype='float64',sep=',')
        real, imag = data[::2], data[1::2]
        
        # builds dataframe with x-axis/frequency
        dataframe=pd.DataFrame(data={'freq':freq,
                                     'Re_S21':real,
                                     'Im_S21':imag},
                               dtype='float64')
        
        self.inst.write('SYSTem:DISPlay:UPDate ONCE')
        self.inst.write('SYSTem:DISPlay:BAR:STOols OFF')
        self.inst.write("DISP:TRAC1:Y:AUTO ONCE")
        # plots plot to lookylook
        if plotter==True:
            plt.figure(1)
            plt.plot(freq,10*np.log(np.abs(real+imag*1j)),'.',
                    label=str(datetime.now()))
            plt.grid()
            plt.title('Insertion loss of forward transmission')
            plt.ylabel('$|S_{21}|$ [dB]')
            plt.xlabel('$f$ [Hz]')
            plt.legend(loc=1)
            
        if savefile==True:
            if not os.path.exists('fsweep_data'):
                os.makedirs('fsweep_data')
            Hstring='H%07i'%int(float(H)*10000)
            name='fsweep_data/%s_%s_T%05i_%s.csv'%(config['sample_name'],
            Hstring,int(float(T)*1000),str(str(datetime.now())).replace(':','-')[:-7])
            
            # save data
            pd.DataFrame.to_csv(dataframe,name)
            del dataframe
            if printer==True:
                print('\nSaved Data successfully!')
        return freq, real, imag
        


###### Old Stuff version 1
"""

# old Version 1.0 from 06.08.2020
# Features:
#     - Printer
#     - Display once (for real)


# measure f_sweep mode
from vna import ZNB40
vna=ZNB40(resource_string='TCPIP0::192.168.1.104::inst0::INSTR')
vna.enter()
s_param=vna.s_parameter(['S21'])
param=vna.parameter(average=5,
                    bandwidth=250,
                    points=1800,
                    start=1e7,
                    stop=1.8e10)
global_param=vna.global_param(bfield=0,temp=8, sample='AB12-27',comment='test test')
config=vna.save_config(s_param,param,global_param)
data=vna.measurement()
vna.show_data(data,config)
vna.save_file(data,config)
vna.__exit__()

import matplotlib.pyplot as plt
class ZNB40():
    def __init__(self, resource_string='TCPIP0::192.168.1.104::inst0::INSTR'):

       # Initialization. Find the resource string with the RsVisaTester or via
       #     import pyvisa
       #     rm = pyvisa.ResourceManager()
       #     print(rm.list_resources())
       #     
       # RSVisa: "AttributeError: 'USBInstrument object has no attribute 'read_bytes'"

        self.resource_string = resource_string

##############################################################################

    def enter(self):

       # Introduces the 'with'-statement. Prepares the analyzer. Does not take
       # any arguments - use __init__ or __call__ to store them.
        
        self.analyzer = RsInstrument(self.resource_string, id_query=True, reset=False)
        # reset the device
        self.analyzer.write_str_with_opc('*RST')
        # delete all old traces
        self.analyzer.write_str_with_opc('CALC:PAR:DEL:ALL')
        # turn continous measurement off
        self.analyzer.write_str('INITiate1:CONTinuous OFF')
        # turn Display to remote control
        self.analyzer.write_str('SYSTem:TSLock SCReen')
        #Displaying the data increases measurement time 
        self.analyzer.write_str_with_opc('SYSTem:DISPlay:UPDate OFF')
        return self

##############################################################################
      
    def s_parameter(self,s_param=['S12','S11'], printer=True):
        # Set the S-Parameter, that should be measured
        # input: ['S11','S22','S12','S21']
        
        # sets a displaypanel with the measured datapoints
        # db mag is default
        self.analyzer.write_str_with_opc("DISP:WIND:STAT ON")
        printers=''
        
        # Each S-Parameter Trace is defined and added to the displaypanel
        for i in range(len(s_param)):
            k=i+1
            self.analyzer.write_str_with_opc("CALC1:PAR:SDEF 'Tr%i', '%s'"%(k,s_param[i]))
            self.analyzer.write_str_with_opc("DISPlay:WINDow:TRAC%i:FEED 'Tr%i'"%(k,k))
            printers=printers+(s_param[i])+', '
        if printer==True:
            print('Setup S-Parameter: %s.'%printers[:-2])
        return s_param
    
##############################################################################
        
    def parameter(self,start=1e5,stop=4e10,points=100001,bandwidth=1e3,power='-10dbm', average=0, sweeptype='linear', printer=True):
        # Sets all the measurement data and return them in a param file
        
        # sets the start frequency, default is 100kHz, input: %i in Hz
        self.analyzer.write_str_with_opc("SENSe1:FREQuency:STARt %i Hz"%start)
        
        # sets the stop frequency, default is , input: %i in Hz
        self.analyzer.write_str_with_opc("SENSe1:FREQuency:STOP %i Hz"%stop)
        
        # sets the amount of datapoints, max is 100001, input: %i
        self.analyzer.write_str_with_opc("SENSe1:SWEep:POINts %i"%points)
        
        # sets the measurement bandwidth, min is 1 Hz, really slow!, input: %i in Hz
        self.analyzer.write_str_with_opc("SENSe1:BANDwidth %i Hz"%bandwidth)
        
        # sets the measurement power, caution you can fry vna!
        # default is -10dbm, input: %s
        self.analyzer.write_str_with_opc("SOURce1:POWer %s"%power)
        
        # sets the measurement mode for x-axis, input: 'lin' (default),'log'
        self.analyzer.write_str_with_opc("SENSe1:SWEep:Type %s"%sweeptype)
        
        # gets approximated measurment time
        time=self.analyzer.query_float('SENSe1:SWEep:TIME?')
        
        # if averaging is greater 0, do it. input: %i
        if average>0:
            self.average(average)
            if printer==True:
                print('%i cycles, within %.1f s will be measured.'%(average,time*average))
        else:
            self.analyzer.write_str_with_opc("SENSe1:AVERage:STATe OFF")
        
        # sets timeout time between measurments to zero
        self.analyzer.write_str_with_opc("SENSe1:SWEep:TIME:AUTO ON")
        
        # build param file
        param ={'start':start,
                'stop':stop,
                'points':points,
                'bandwidth':bandwidth,
                'power':power,
                'sweeptype':sweeptype,
                'average':average,
                'sweeptime':time}
        
        if printer==True:
            print('\nThe parameter are:')
            print('start frequency = %i Hz'%start)
            print('stop frequency = %i Hz'%stop)
            print('sweep points = %i'%points)
            print('bandwidth = %i Hz'%bandwidth)
            print('power = '+power)
            print('\nThe sweep is done in %s mode.'%sweeptype)
            print('\nThe cycle will need %.1f s.'%time)
            
        return param

##############################################################################
        
    def average(self, average=3):
        # setup single point averaging
        
        # sets the averaging number
        self.analyzer.write_str_with_opc("SENSe1:AVERage:COUNt %i"%average)
        
        # activate averaging
        self.analyzer.write_str_with_opc("SENSe1:AVERage:STATe ON")
        
        # delete the data from last averaging
        self.analyzer.write_str_with_opc("SENSe1:AVERage:CLEar")
        
        # sets amount of sweeps, that have to be done in order to average
        self.analyzer.write_str_with_opc("SENSe1:SWEep:COUNt %i"%average)

##############################################################################
        
    def measurement(self, printer=True):
        # shows measured data once. (is better for performance)
        self.analyzer.write_str_with_opc('SYSTem:DISPlay:UPDate OFF')
        
        # does the measurement and gets data
        count=int(self.analyzer.query_int('SENSe1:SWEep:COUNt?'))
        
        # gets maximum timeout time, to prevent errors during long time meas.
        timeout=self.analyzer.query_float('SENSe1:SWEep:TIME?')
        timeout=(timeout*count*1.2+10)*1000
        
        # initialize measurement
        self.analyzer.write_str_with_opc("INIT",timeout=timeout)
        if printer==True:
            print('\nMeasurement done successfully!')
        
        # shows measured data once. (is better for performance)
        self.analyzer.write_str_with_opc('SYSTem:DISPlay:UPDate ONCE')
        
        # gets x-axis/frequency data
        freq = self.analyzer.query_bin_or_ascii_float_list('CALC1:DATA:STIM?')
        freq=np.array(freq)
        
        # builds dataframe with x-axis/frequency
        dataframe=pd.DataFrame(data={'frequency':freq}, dtype='float32')
        
        # looks for active traces and iterate over them
        param=self.analyzer.query_str('CALCulate1:PARameter:CATalog?')
        param=param[1:-1].split(',')
        
        for i in range(int(len(param)/2)):
            trace=param[i*2]
            name_S=param[i*2+1]
            
            query_str = "FORM REAL,32;CALC1:DATA:TRACe? '%s', SDAT"%trace
            sdata = self.analyzer.query_bin_or_ascii_float_list(query_str)
            reals, imags = list(), list()
            reals.append(np.asarray(sdata[::2], dtype=np.float32))
            imags.append(np.asarray(sdata[1::2], dtype=np.float32))
            S=(np.array(reals).transpose()+np.array(imags).transpose()*1j)[:,0]
            dataframe[name_S]=S
        if printer==True:
            print('\nGot Data successfully!')
        return dataframe

##############################################################################
    
    def global_param(self, 
                     bfield=0,
                     temp=300, 
                     sample='plane', 
                     comment='no comment'):
        global_param={'bfield':bfield,
                      'temperature':temp,
                      'sample':sample,
                      'comment':comment}
        return global_param
                        
##############################################################################
    
    def save_config(self,s_param,param, global_param, printer=True):        
        # Save Config File

        # get current time stamp
        date=str(datetime.now()) 
        
        # builds config file
        config={'timestamp':date,
                's_param':str(s_param),
                'start':param['start'],
                'stop':param['stop'],
                'points':param['points'],
                'bandwidth':param['bandwidth'],
                'power':param['power'],
                'sweeptype':param['sweeptype'],
                'average':param['average'],
                'sweeptime':param['sweeptime'],
                'bfield':global_param['bfield'],
                'temperature':global_param['temperature'],
                'sample':global_param['sample'],
                'comment':global_param['comment']}
        
        # append config file to current conig.json 
        with open('config.json','a+') as f:
            json.dump(config,f,indent=1)
        
        if printer==True:
            print('\nSaved configuration successfully!')
        return config

##############################################################################
   
    def show_data(self, data, config, fig=0):
        # shows the measured data in one plot
        plt.close('all')
        plt.figure(fig)
        plt.figure(figsize=(16,9), facecolor='w', edgecolor='k')
        plt.xlabel('frequency $f$ [Hz]')
        plt.ylabel('S-Parameter $|S|^2$ (a.u.)')
        x=data['frequency']
        for i in range(data.shape[1]-1):
            y=np.abs(data[data.columns[i+1]])**2
            plt.semilogy(x,y,'.',label=data.columns[i+1])
        plt.grid()
        plt.legend(loc='upper right')

        # build name        
        name='showdata'
        name=name+'_%s'%config['sample']
        name=name+'_T%06i'%int(float(config['temperature'])*1000)
        name=name+'_B%06i'%int(float(config['bfield'])*10000)
        name=name+'_%s.pdf'%str(config['timestamp']).replace(':','-')[:-7]
        plt.savefig(name,
                    bbox_inches='tight',
                    transparent=True,
                    pad_inches=0.1,
                    format='pdf')

##############################################################################
    
    def save_file(self, data, config, printer=True):
        # saves dataframe
        
        # build name
        name='data/data'
        name=name+'_%s'%config['sample']
        name=name+'_T%06i'%int(float(config['temperature'])*1000)
        name=name+'_B%06i'%int(float(config['bfield'])*10000)
        name=name+'_%s.csv'%str(config['timestamp']).replace(':','-')[:-7]
        
        # save data
        pd.DataFrame.to_csv(data,name)
        del data
        if printer==True:
            print('\nSaved Data successfully!')
        return

##############################################################################        
## Under writing. Not good enough yet
# check vna manual p133


    def time_domain_reflectometry(self,dataframe):
        fft_data, real_data = pd.DataFrame(), pd.DataFrame()
        fft_data['time']=(1/dataframe.frequency)
        real_data['distance']=fft_data['time']/2*3e8
        error=True
        for i in range(dataframe.shape[1]-1):
            name=dataframe.columns[i+1]
            if name[1]==name[2]:
                name_fft=name[:-3]+'*(t)'
                name_real='R_'+name[1:-3]+'(d)'
                fft_data[name_fft]=np.fft.ifft(dataframe[name])
                real_data[name_real]=np.abs(fft_data[name_fft])**2
                error=False
        if error == True:
            print('ERROR: no suiting S parameter for TDR found!')
        return fft_data, real_data
        
    def plot_time_domain_reflectometry(self,real_data,maxlen=2):
        xaxis=real_data.columns[0]
        x=np.array(real_data[xaxis])
        for i in range(real_data.shape[1]-1):
            name=real_data.columns[i+1]
            y=np.array(real_data[name])
            y[x<=0.005]=np.nan  
            y[x>=2*maxlen]=np.nan
            plt.figure(i)
            plt.figure(figsize=(16, 9), dpi= 300, facecolor='w', edgecolor='k')
            plt.semilogy(x,y,'r.-')
            plt.grid()
            plt.xlim([0,maxlen*1.2])
            plt.ylabel('Reflexion coefficient %s (a.u.)'%name)
            plt.xlabel('%s [m]'%xaxis)
            plt.title('')

##############################################################################
    # System relevante Operationen        
    
    def __exit__(self):
    #def __exit__(self, exception_type, exception_value, traceback):
        self.analyzer.close()
        
    def DisplayOff(self):
        self.analyzer.write_str_with_opc('SYSTem:DISPlay:UPDate OFF')
        #Displaying the data increases measurement time 
        print('turn display off')
        
    def DisplayOn(self):
        self.analyzer.write_str_with_opc('SYSTem:DISPlay:UPDate ON')
        #Displaying the data increases measurement time 
        print('turn display on')
        
    def DisplayOnce(self):
        self.analyzer.write_str_with_opc('SYSTem:DISPlay:UPDate ONCE')
        print('turn display once')
            
    def unlock(self):
        # unlock and turn on screen for local operation
        self.analyzer.write_str('SYSTem:TSLock OFF')
        self.analyzer.write_str_with_opc('SYSTem:DISPlay:UPDate ON')
        return self
"""