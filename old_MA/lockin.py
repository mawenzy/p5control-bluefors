#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Current Version from: 01.10.'20
Features:
- get configuration

@author: Oliver I.

e.g.:
# Get Lock-In Settings
from driver.lockin import SR830
lockin_U=SR830(GPIB_No= 8)
lockin_I=SR830(GPIB_No=10)
lockin_U.get_config(printer=True, saveconfig=False)
lockin_I.get_config(printer=True, saveconfig=False)
lockin_U.exit()
lockin_I.exit()
"""
import pyvisa
import json, os
import numpy as np
from datetime import datetime

class SR830():
    def __init__(self, GPIB_No=8):
        # schwarze VISA Magie
        # input spezification
        rm=pyvisa.ResourceManager()
        inst=rm.open_resource('GPIB0::%i::INSTR'%GPIB_No,
                              write_termination='\n',
                              read_termination='\n')
        self.inst=inst
        self.inst.write('*CLS')
        
    def exit(self):
        self.inst.close()
        
    def get_config(self,
                   printer=False,
                   save_config=False):
        name=str(self.inst)
        date=str(datetime.now()) 
        if printer==True:
            print("\nSR830 = '%s'"%name)
            print("timestamp = '%s'"%date)
        while True:
            try:
                # Time Constant Group
                time_constant=self.get_time_constant(printer=printer)
                time_slope_oct=self.get_time_slope_oct(printer=printer)
                time_sync_filter=self.get_time_sync_filter(printer=printer)

                # Signal Input Group
                signal_input=self.get_signal_input(printer=printer)
                signal_couple=self.get_signal_couple(printer=printer)
                signal_ground=self.get_signal_ground(printer=printer)

                # Sensitivity, Reserve & Filters Group
                sensitivity=self.get_sensitivity(printer=printer)
                reserve=self.get_reserve(printer=printer)
                filter_notch=self.get_filter_notch(printer=printer)

                # Reference Group
                ref_phase=self.get_ref_phase(printer=printer)
                ref_frequency=self.get_ref_frequency(printer=printer)
                ref_amplitude=self.get_ref_amplitude(printer=printer)
                ref_harmonic=self.get_ref_harmonic(printer=printer)
                ref_trigger=self.get_ref_trigger(printer=printer)
                ref_source=self.get_ref_source(printer=printer)

                # Channel Group
                ch1_display=self.get_ch1_display(printer=printer)
                ch1_ratio=self.get_ch1_ratio(printer=printer)
                ch1_output=self.get_ch1_output(printer=printer)

                ch2_display=self.get_ch2_display(printer=printer)
                ch2_ratio=self.get_ch2_ratio(printer=printer)
                ch2_output=self.get_ch2_output(printer=printer)

                # Offset & Expand Group
                output_offset_X=self.get_output_offset_X(printer=printer)
                output_offset_Y=self.get_output_offset_Y(printer=printer)
                output_offset_R=self.get_output_offset_R(printer=printer)

                output_expand_X=self.get_output_expand_X(printer=printer)
                output_expand_Y=self.get_output_expand_Y(printer=printer)
                output_expand_R=self.get_output_expand_R(printer=printer)
                break
            except IndexError:
                print('Please restart SR830!')
                
        config={'SR830':name,
                'timestamp':date,
                '# Time Constant Group':' ',
                'time_constant':time_constant,
                'time_slope_oct':time_slope_oct,
                'time_sync_filter':time_sync_filter,
                '# Signal Input Group':' ',
                'signal_input':signal_input,
                'signal_couple':signal_couple,
                'signal_ground':signal_ground,
                '# Sensitivity, Reserve & Filters Group':' ',
                'sensitivity':sensitivity,
                'reserve':reserve,
                'filter_notch':filter_notch,
                '# Reference Group':' ',
                'ref_phase':ref_phase,
                'ref_frequency':ref_frequency,
                'ref_amplitude':ref_amplitude,
                'ref_harmonic':ref_harmonic,
                'ref_trigger':ref_trigger,
                'ref_source':ref_source,
                '# Channel Group':' ',
                'ch1_display':ch1_display,
                'ch1_ratio':ch1_ratio,
                'ch1_output':ch1_output,
                'ch2_display':ch2_display,
                'ch2_ratio':ch2_ratio,
                'ch2_output':ch2_output,
                '# Offset & Expand Group':' ',
                'output_offset_X':output_offset_X,
                'output_offset_Y':output_offset_Y,
                'output_offset_R':output_offset_R,
                'output_expand_X':output_expand_X,
                'output_expand_Y':output_expand_Y,
                'output_expand_R':output_expand_R}

        if save_config==True:
            # generates config path, if not made yet
            path='config'
            if not os.path.exists(path):
                os.makedirs(path)
            # dumps config in file
            with open('config/SR830_config.json','a+') as f:
                json.dump(config,f,indent=1)
        return config
    
    def get_ref_phase(self, printer=False):
        phase=float(self.inst.query('PHAS?'))
        if printer==True:
            print('reference phase [deg]= %3.2f'%phase)
        return phase
    
    def get_ref_frequency(self, printer=False):
        freq=float(self.inst.query('FREQ?'))
        if printer==True:
            print('reference frequency [Hz]= %6.3f'%freq)
        return freq
    
    def get_ref_amplitude(self, printer=False):
        ampl=float(self.inst.query('SLVL?'))
        if printer==True:
            print('reference amplitude [V] = %1.3f'%ampl)
        return ampl
    
    def get_ref_harmonic(self, printer=False):
        harm=float(self.inst.query('HARM?'))
        if printer==True:
            print("reference harmonics = %i"%harm)
        return harm
    
    def get_ref_trigger(self, printer=False):
        spez=['sine','pos edge','neg edge']
        rt=int(self.inst.query('RSLP?'))
        rt=spez[rt]
        if printer==True:
            print("reference trigger = '%s'"%rt)
        return rt
    
    def get_ref_source(self, printer=False):
        spez=['NOT internal','internal']
        ri=int(self.inst.query('FMOD?'))
        ri=spez[ri]
        if printer==True:
            print("reference source = '%s'"%ri)
        return ri
    
    def get_signal_input(self, printer=False):
        spez=['A','A-B','I (10^6)','I (10^8)']
        isrc=int(self.inst.query('ISRC?'))
        isrc=spez[isrc]
        if printer==True:
            print("signal input = '%s'"%isrc)
        return isrc
    
    def get_signal_couple(self, printer=False):
        spez=['AC','DC']
        icpl=int(self.inst.query('ICPL?'))
        icpl=spez[icpl]
        if printer==True:
            print("signal couple = '%s'"%icpl)
        return icpl
    
    def get_signal_ground(self, printer=False):
        spez=['FLOAT','GROUND']
        ignd=int(self.inst.query('IGND?'))
        ignd=spez[ignd]
        if printer==True:
            print("signal ground = '%s'"%ignd)
        return ignd
    
    def get_filter_notch(self, printer=False):
        spez=['no filters','Line notch','2x Line notch',
              'Both notch filters']
        ilin=int(self.inst.query('ILIN?'))
        ilin=spez[ilin]
        if printer==True:
            print("filter = '%s'"%ilin)
        return ilin
    
    def get_reserve(self, printer=False):
        spez=['HIGH RESERVE','NORMAL','LOW RESERVE']
        rmod=int(self.inst.query('RMOD?'))
        rmod=spez[rmod]
        if printer==True:
            print("reserve = '%s'"%rmod)
        return rmod

    def get_sensitivity(self, printer=False):
        spez=[2e-9,5e-9,1e-8,2e-8,5e-8,1e-7,2e-7,5e-7,1e-6,2e-6,
              5e-6,1e-5,2e-5,5e-5,1e-4,2e-4,5e-4,1e-3,2e-3,5e-3,
              1e-2,2e-2,5e-2,1e-1,2e-1,5e-1,1] #V/uA
        sens=int(self.inst.query('SENS?'))
        sens=spez[sens]
        if printer==True:
            print("sensitivity = %s"%sens)
        return sens
    
    def get_time_constant(self, printer=False):
        spez=[1e-5,3e-5,1e-4,4e-4,1e-3,3e-3,1e-2,3e-2,1e-1,
          3e-1,1e0,3e0,1e1,3e1,1e2,3e2,1e3,3e3,1e4,3e4] #s
        oflt=int(self.inst.query('OFLT?'))
        oflt=spez[oflt]
        if printer==True:
            print("time constant = %s"%oflt)
        return oflt
        
    def get_time_slope_oct(self, printer=False):
        spez=[' 6 dB','12 dB','18 dB','24 dB']
        ofsl=int(self.inst.query('OFSL?'))
        ofsl=spez[ofsl]
        if printer==True:
            print("Slope/Oct = '%s'"%ofsl)
        return ofsl
    
    def get_time_sync_filter(self, printer=False):
        spez=['Off','SYNC < 200 Hz']
        sync=int(self.inst.query('SYNC?'))
        sync=spez[sync]
        if printer==True:
            print("Sync Filter = '%s'"%sync)
        return sync
    
    def get_ch1_display(self, printer=False):
        ddef=list(self.inst.query('DDEF? 1').split(','))
        spez=['X','R','X Noice','Aux1','Aux2']
        disp=spez[int(ddef[0])]
        if printer==True:
            print("CH1 display = '%s'"%disp)        
        return disp
    
    def get_ch1_ratio(self, printer=False):
        ddef=list(self.inst.query('DDEF? 1').split(','))
        spez=['none','Aux1','Aux2']
        rati=spez[int(ddef[1])]
        if printer==True:
            print("CH1 ratio = '%s'"%rati)
        return rati
        
    def get_ch2_display(self, printer=False):
        ddef=list(self.inst.query('DDEF? 2').split(','))
        spez=['Y','theta','Y Noice','Aux3','Aux4']
        disp=spez[int(ddef[0])]
        if printer==True:
            print("CH2 display = '%s'"%disp)        
        return disp
    
    def get_ch2_ratio(self, printer=False):
        ddef=list(self.inst.query('DDEF? 2').split(','))
        spez=['none','Aux3','Aux4']
        rati=spez[int(ddef[1])]
        if printer==True:
            print("CH2 ratio = '%s'"%rati)
        return rati
    
    def get_ch1_output(self, printer=False):
        spez=['CH1 Display','X']
        fpop=int(self.inst.query('FPOP? 1'))
        fpop=spez[fpop]
        if printer==True:
            print("CH1 output = '%s'"%fpop)
        return fpop
        
    def get_ch2_output(self, printer=False):
        spez=['CH2 Display','Y']
        fpop=int(self.inst.query('FPOP? 2'))
        fpop=spez[fpop]
        if printer==True:
            print("CH2 output = '%s'"%fpop)
        return fpop
    
    # AOFF
    def get_output_offset_X(self, printer=False):
        oexp=list(self.inst.query('OEXP? 1').split(','))
        offset=np.float(oexp[0])
        if printer==True:
            print("output offset X= %3.2f"%offset)
        return offset
    def get_output_offset_Y(self, printer=False):
        oexp=list(self.inst.query('OEXP? 2').split(','))
        offset=np.float(oexp[0])
        if printer==True:
            print("output offset Y= %3.2f"%offset)
        return offset
    def get_output_offset_R(self, printer=False):
        oexp=list(self.inst.query('OEXP? 3').split(','))
        offset=np.float(oexp[0])
        if printer==True:
            print("output offset R= %3.2f"%offset)
        return offset
        
    def get_output_expand_X(self, printer=False):
        oexp=list(self.inst.query('OEXP? 1').split(','))
        spez=[1,10,100]
        expand=spez[int(oexp[1])]
        if printer==True:
            print("output expand X = %i"%expand)
        return expand
    def get_output_expand_Y(self, printer=False):
        oexp=list(self.inst.query('OEXP? 2').split(','))
        spez=[1,10,100]
        expand=spez[int(oexp[1])]
        if printer==True:
            print("output expand Y = %i"%expand)
        return expand
    def get_output_expand_R(self, printer=False):
        oexp=list(self.inst.query('OEXP? 3').split(','))
        spez=[1,10,100]
        expand=spez[int(oexp[1])]
        if printer==True:
            print("output expand R = %i"%expand)
        return expand