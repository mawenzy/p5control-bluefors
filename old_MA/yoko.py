# -*- coding: utf-8 -*-
"""
Current Version from: 09.10.'20
Features:
- initialize
- exit
- get_setting
- get_status
- get_sweep_info
- output_on
- output_off
- set_rangeV(max_voltage)
- set_rangeI(max_current)
- set_current_limit(max_current)
- setup_V(voltage) # no outout
- setup_V_sweep(V_points,sweep_time,mode)
- start_sweep

@author: Oliver I.
Many Thanks to: Lukas Kammermeier

e.g.:
from yoko import Yokogawa7651
from time import sleep

yoko=Yokogawa7651()
yoko.initialize()

# set constant voltage
yoko.set_current_limit(max_current=.11)
yoko.setup_V(voltage=-3e-3)
yoko.output_on()
sleep(3)
yoko.output_off()

# set voltage sweep
yoko.set_current_limit(max_current=.11)
yoko.setup_V_sweep(V_points=[-1e-2,1e-2,-1e-2], #from -10mV to 10mV and back
                    sweep_time=3, #s
                    mode='single') #else 'continous'
yoko.start_sweep()
while yoko.get_sweep_info()==True:
    print('sweep running!', end=" \r")
print('sweep ended...')

#get config and status
yoko.get_setting(printer=True, save_config=True)
yoko.get_status(printer=True, save_status=True)
yoko.exit()
"""

import pyvisa
import json, os
import numpy as np
from datetime import datetime

class Yokogawa7651():
    
    def __init__(self, GPIB_No=3):
        # black VISA magic
        rm=pyvisa.ResourceManager()
        inst=rm.open_resource('GPIB0::%i::INSTR'%GPIB_No,
                              read_termination='\r\n',
                              write_termination='\r\n')
        self.inst=inst
        self.gpib=GPIB_No
        
    def initialize(self):
        # Setting initialization 6-26
        self.inst.write('RC')
        # o output, 0 off, e trigger
        self.inst.write('O0E')
        
    def exit(self):
        self.inst.close()
    
    def get_setting(self, printer=False,save_config=False):
        # idn
        self.idn=self.inst.query('OS')
        
        frs=self.inst.read()
        spezFR={'F1R2':['DC V','10mV'],
                'F1R3':['DC V','100mV'],
                'F1R4':['DC V','1V'],
                'F1R5':['DC V','10V'],
                'F1R6':['DC V','30V'],
                'F5R4':['DC A','1mA'],
                'F5R5':['DC A','10mA'],
                'F5R6':['DC A','100mA']}
        FR=spezFR[frs[:4]]
        self.F=FR[0]
        self.R=FR[1]
        self.S=float(frs[5:-1]) # A/V
        
        piswm=self.inst.read()
        spezM={'M0':'Repeat Mode',
               'M1':'Single Mode'}
        SW_ind=int(piswm.index('S'))
        M_ind=int(piswm.index('M'))
        self.PI=float(piswm[2:SW_ind]) #s
        self.SW=float(piswm[SW_ind+2:M_ind]) #s
        self.M=spezM[piswm[M_ind:]]
        
        lvla=self.inst.read()
        LA_ind=int(lvla.index('A'))-1
        self.LV=int(lvla[2:LA_ind]) #V
        self.LA=int(lvla[LA_ind+2:]) #mA
        
        end=self.inst.read()
        
        date=str(datetime.now())
        config={'Yokogawa7651:':'setting',
                'timestamp':date,
                'idn':self.idn,
                'function_setting':self.F,
                'range_setting':self.R,
                'data_setting':self.S,
                'program_interval':self.PI,
                'sweep_setting':self.SW,
                'run_mode':self.M,
                'voltage_limit':self.LV,
                'current_limit':self.LA}
        
        if printer==True:
            print("\nYoko settings:",
                  "\nidn = '%s'"%self.idn,
                  "\nfunction_setting = '%s'"%self.F,
                  "\nrange_setting = '%s'"%self.R,
                  "\ndata_setting = %+012.4E V/A"%self.S,
                  "\nprogram_interval = %4.1f s"%self.PI,
                  "\nsweep_setting = %4.1f s"%self.SW,
                  "\nrun_mode = '%s'"%self.M,
                  "\nvoltage_limit = %i V"%self.LV,
                  "\ncurrent_limit = %i mA"%self.LA)
            
        # save config
        if save_config==True:
            # generates config path, if not made yet
            path='config'
            if not os.path.exists(path):
                os.makedirs(path)
            # dumps config in file
            with open('config/Yokogawa7651_config.json','a+') as f:
                json.dump(config,f,indent=1)
        return config
        
    def get_status(self, printer=False, save_status=False):
        oc='%08i'%int(bin(int(self.inst.query('OC')[5:]))[2:])
        
        if printer==True or save_status==True:
            spezOC={'CAL_switch':['OFF','ON'],
                    'IC_memory_card':['OUT','IN'],
                    'calibration_mode':['normal','calibration'],
                    'output_status':['OFF','ON'],
                    'output_stable':['normal','unstable'],
                    'previous_error':['ok','error'],
                    'program_execution':['normal','under execution'],
                    'program_setting':['normal','under setting']}

            CAL_switch=spezOC['CAL_switch'][int(oc[0])]
            IC_memory_card=spezOC['IC_memory_card'][int(oc[1])]
            calibration_mode=spezOC['calibration_mode'][int(oc[2])]
            output_status=spezOC['output_status'][int(oc[3])]
            output_stable=spezOC['output_stable'][int(oc[4])]
            previous_error=spezOC['previous_error'][int(oc[5])]
            program_execution=spezOC['program_execution'][int(oc[6])]
            program_setting=spezOC['program_setting'][int(oc[7])]
            
            if printer==True:
                print('\nYoko status:')
                print("CAL_switch = '%s'"%CAL_switch)
                print("IC_memory_card = '%s'"%IC_memory_card)
                print("calibration_mode = '%s'"%calibration_mode)
                print("output_status = '%s'"%output_status)
                print("output_stable = '%s'"%output_stable)
                print("previous_error = '%s'"%previous_error)
                print("program_execution = '%s'"%program_execution)
                print("program_setting = '%s'"%program_setting)
            
            if save_status==True:   
                # generates config path, if not made yet
                path='config'
                if not os.path.exists(path):
                    os.makedirs(path)
                # Save Status to Config File
                date=str(datetime.now())
                status={'Yokogawa7651:':'status',
                        'timestamp':date,
                        'CAL_switch':CAL_switch,
                        'IC_memory_card':IC_memory_card,
                        'calibration_mode':calibration_mode,
                        'output_status':output_status,
                        'output_stable':output_stable,
                        'previous_error':previous_error,
                        'program_execution':program_execution,
                        'program_setting':program_setting}      
                # append config file to current conig.json 
                with open('config/Yokogawa7651_status.json','a+') as f:
                    json.dump(status,f,indent=1)
        return oc
                
    def get_sweep_info(self):
        oc='%08i'%int(bin(int(self.inst.query('OC')[5:]))[2:])
        return bool(int(oc[6]))
    
    def output_on(self):
        self.inst.write('O1E')
        
    def output_off(self):
        self.inst.write('O0E')
        
    def set_rangeV(self, max_voltage=30):
        max_voltage=np.abs(max_voltage)
        if   max_voltage<=1e-2:
            self.inst.write('F1R2')
        elif max_voltage<=1e-1:
            self.inst.write('F1R3')
        elif max_voltage<=1e+0:
            self.inst.write('F1R4')
        elif max_voltage<=1e+1:
            self.inst.write('F1R5')
        elif max_voltage<=3e+1:
            self.inst.write('F1R6')
        else:
            print('ERROR: Voltage Range is too high!')
            
    def set_rangeI(self, max_current=1.2e-1):
        if   max_current<=1e-3:
            self.inst.write('F5R4E')
        elif max_current<=1e-2:
            self.inst.write('F5R5E')
        elif max_current<=1.2e-1:
            self.inst.write('F5R6E')
        else:
            print('ERROR: Current Range is too high!')
    
    # set current limit in V mode,
    # in order to prevent damage at DUT
    def set_current_limit(self, max_current=.12):
        self.inst.write('LA%3i'%(max_current*1000))
    
    def setup_V(self, voltage=-1.2345e-3):
        self.output_off()
        if np.abs(voltage)>3e1:
            print('ERROR: Voltage is too high!')
            self.inst.write('S-0E0E')
        else:
            self.set_rangeV(max_voltage=voltage)
            self.inst.write('S%+012.4EE'%voltage)
            

        
    def setup_V_sweep(self,
                    V_points=[-1e-2,1e-2,-1e-2],
                    sweep_time=3,
                    mode='single'):
        self.output_off()
        # set V mode and appropiate range automatic
        self.set_rangeV(max_voltage=float(np.max(np.abs(V_points))))
        # set first point as starting point
        self.setup_V(voltage=V_points[0])
        # start programm settings
        self.inst.write('PRS')
        # define start and end point
        for V in V_points[1:]:
            self.inst.write('S%+012.4E'%V)
        # end programm settings
        self.inst.write('PRE')
        # PI=SW for triangular shape
        self.inst.write('PI%06.1f'%sweep_time)
        self.inst.write('SW%06.1f'%sweep_time)
        # set (single) sweep mode
        if mode=='continous':
            self.inst.write('M0')
        else:
            self.inst.write('M1')
        # trigger all the input
        self.inst.write('E')
        
    def start_sweep(self):
        # output on & start the sweep
        self.inst.write('O1E;RU2')
        