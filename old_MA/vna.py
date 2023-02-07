# -*- coding: utf-8 -*-
"""
Created on Fri Jun 26 15:06:25 2020

current Version from 06.08.2020
Features:
    - Printer
    - Display once (for real)

@author: Oliver I.
Many Thanks to: Lukas Kammermeier und Lukas Siedentop

Bspw:
from driver.vna import ZNB40
VNA=ZNB40(resource_string='TCPIP0::192.168.1.104::inst0::INSTR')
VNA.enter()
s_param=VNA.s_parameter(['S11','S22','S12','S21'])
param=VNA.parameter(start=1e5, average=1, bandwidth=10000, points=100)
data=VNA.measurement()
config=VNA.save_config(s_param,param)
VNA.show_data(data,config)
VNA.save_file(data,config)   
"""
from RsInstrument.RsInstrument import RsInstrument
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from datetime import datetime

class ZNB40():
    def __init__(self, resource_string='TCPIP0::192.168.1.104::inst0::INSTR'):
        """
        Initialization. Find the resource string with the RsVisaTester or via
            import pyvisa
            rm = pyvisa.ResourceManager()
            print(rm.list_resources())
            
        RSVisa: "AttributeError: 'USBInstrument object has no attribute 'read_bytes'"
        """
        self.resource_string = resource_string

##############################################################################

    def enter(self):
        """
        Introduces the 'with'-statement. Prepares the analyzer. Does not take
        any arguments - use __init__ or __call__ to store them.
        """
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
    
    
########################################
########################################
        
    # old stuff
########################################
       
    
##############################################################################
        
    def measurement_old(self):
        # does the measurement and gets data
        
        # gets maximum timeout time, to prevent errors during long time meas.
        timeout=self.analyzer.query_float('SENSe1:SWEep:TIME?')*1200+10000
        
        # initialize measurement
        self.analyzer.write_str_with_opc("INIT",timeout=timeout)
        
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
            
            # gets data from iterated trace
            query_str = "FORM REAL,32;CALC1:DATA:TRACe? '%s', SDAT"%trace
            sdata = self.analyzer.query_bin_or_ascii_float_list(query_str)
            
            # append data to dataframe
            reals, imags = list(), list()
            reals.append(np.asarray(sdata[::2], dtype=np.float32))
            imags.append(np.asarray(sdata[1::2], dtype=np.float32))
            S=(np.array(reals).transpose()+np.array(imags).transpose()*1j)[:,0]
            dataframe[name_S]=S
        print('\nMeasurement done successfully!')
        return dataframe
    
    
    
    def time_domain_reflectometry_old(self,freq,data,s_param):
        R_space=np.zeros((data.shape),dtype='float32')
        for i in range(data.shape[1]):
            R_space[:,i]=np.abs(np.fft.ifft(data[:,i]))**2
        time=(1/freq)
        space=time/2*3e8
        print('\nFourier Transformed successfully!')
        return R_space, space,s_param
    
    def plot_time_domain_reflectometry_old(self,space,R_space,s_param,maxlen=2):
        R_space[space<=0.005,:]=np.nan #ignore stecker
        for i in range(R_space.shape[1]):
            plt.figure(i)
            plt.semilogy(space,R_space[:,i],'r.-')
            plt.grid()
            plt.xlim([0,maxlen*1.2])
            plt.ylabel('Reflectioncoefficient |S|² (a.u.)')
            plt.xlabel('distance [m]')
            plt.title('')
    
        


        
    def get_S_parameter(self):
        """
        Return the currently measured S-Parameter
        """
        
        s_param = self.analyzer.query_str('CALC1:PAR:CAT?').split(',')[-1]
        # omit the last dash
        return s_param[:-1]
    def write_str_with_opc(self, command):
        self.analyzer.write_str_with_opc("%s"%command, timeout=360000000)
        
    def query_str(self, command):
        self.analyzer.query_str("%s"%command)
    def query_float(self, command):
        self.analyzer.query_float("%s"%command)
        
    def frequency_domain(self):
        """
        Get the frequency values at which is measured.
        """
        #paras = self.parameters()
        #start = paras['Start [GHz]']*1e9
        #stop = paras['Stop [GHz]']*1e9
        #n = paras['Sample Points']
        #return np.linspace(start, stop, n)
        
        data = self.analyzer.query_bin_or_ascii_float_list('CALC1:DATA:STIM?')
        return data
    
    def data(self, trace):
        # read raw data byte-array directly, formatting manually
        query_str = "FORM REAL,32;CALC1:DATA:TRACe? '%s', SDAT"%trace
        # query_str = 'FORM ASC;CALC:DATA:ALL? SDAT'
        
        reals = list()
        imags = list()
        data = self.analyzer.query_bin_or_ascii_float_list(query_str)
        reals.append(np.asarray(data[::2], dtype=np.float32))
        imags.append(np.asarray(data[1::2], dtype=np.float32))
        return reals, imags
            
    def Measurement_old(self):
        self.analyzer.write_str_with_opc("INIT",timeout=3600000)
        # timeout is 1h
        freq = self.analyzer.query_bin_or_ascii_float_list('CALC1:DATA:STIM?')
        freq=np.array(freq)
        param=self.analyzer.query_str('CALCulate1:PARameter:CATalog?')
        param=param[1:-1]+','
        length=(len(param)+1)%8+1
        s_param=list()
        data=np.zeros((len(freq),length),dtype='complex64')
        for i in range(length):
            trace=param[i*8:i*8+3]
            s_param.append(str(param[i*8+4:i*8+7]))
            query_str = "FORM REAL,32;CALC1:DATA:TRACe? '%s', SDAT"%trace
            sdata = self.analyzer.query_bin_or_ascii_float_list(query_str)
            reals, imags = list(), list()
            reals.append(np.asarray(sdata[::2], dtype=np.float32))
            imags.append(np.asarray(sdata[1::2], dtype=np.float32))
            s=(np.array(reals).transpose()+np.array(imags).transpose()*1j)[:,0]
            data[:,i]=s[:]
        print('\nMeasurement done successfully!')
        return freq,data,s_param   