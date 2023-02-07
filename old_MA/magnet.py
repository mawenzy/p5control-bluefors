# -*- coding: utf-8 -*-
"""
TODO:
- comment tha shit out of this function! please!
- implement factor for AM430

Current Version from 09.12.'20
- featuring AM430 / BlueFors
- featuring IPS120 / Scheer III

Current Version from: 25.09.'20
Features:
- implementing factor for max rate

Current Version from: 06.08.'20
Features:
- printer implemented

Version from: 06.07.'20
Features:
- negative magnetic field support
- reducing to funtion goto with optional rate input
- change rate on the fly, while in max mode
- "printer" consitency
- error if field is to high

@author: Oliver I.
Many Thanks to: Lukas Kammermeier

e.g.:
# Set magnetic field
from driver.magnet import IPS120_10
magnet=IPS120_10()
magnet.reinitialize()
magnet.goto(0.1,factor=.7)
magnet.readfield(printer=True)
magnet.turn_off()
magnet.exit()


or e.g.:
from driver.magnet import AM430
magnet=AM430()
magnet.reinitialize()
magnet.goto(.01,rate=.1)
magnet.readfield(printer=True)
magnet.goto(.02,factor=.7)
magnet.readfield(printer=True)
magnet.turn_off()
magnet.exit()
"""

from time import sleep
import pyvisa
import numpy as np


##############################################################################
##############################################################################
class IPS120_10():
    def __init__(self, GPIB_No=25):
        # initialisiert Magneten, schwarze VISA Magie
        # input spezification
        rm=pyvisa.ResourceManager()
        inst=rm.open_resource('GPIB0::%i::INSTR'%GPIB_No,
                              read_termination='\r',
                              write_termination='\r')
        self.inst=inst
        
    def exit(self):
        self.inst.close()
        

##############################################################################
    def reinitialize(self, printer=False):
        # set magnet parameter
        # TODO check which heater works
        try:
            self.inst.write('$C3')     #remote & unlocked        
            sleep(0.1)
            self.inst.write('$Q4')     #four digits extended resolution            
            self.inst.write('$M1')     #set mode, units "tesla", fast   
            sleep(0.1)
            self.inst.write('$H1')     #switch heater on
            sleep(0.1)
            self.inst.write('$A0')     #hold operation
            self.inst.heater=True      # switch heater on
            if printer==True:
                print('Magnet Initializing...Please Wait 10s')
            for i in range (10): #waits for 30s??
                sleep(1)
                pass
        except:
            print('ERROR: magnet initialization failed')
            return False
        if printer==True:
            print('Done Initializing')
            
##############################################################################
    # Simple function to read/set the current rate/field
        # all numbers dimension is T/min
        # printer=False prevent from printing (default: True)
        # redundant check if setrate is higher than 0.723 (ScheerIII)
        # TODO make them consistent!
        
    def readrate(self, printer=False):
        rate=float(self.inst.query('R9')[1:])
        if printer==True:
            print('current rate is %5.4f T/min.'%rate)
        return rate
    
    def setrate(self, sweeprate, printer=False):
        if sweeprate>=(0.723):
            sweeprate=0.723
            print('rate is reduced!')            
        self.inst.write('$T%4.3f'%sweeprate)
        sleep(0.1)
        if printer==True:
            rate=self.readrate(printer=True)
        else:
            rate=self.readrate()
        return rate

    def readfield(self,printer=False):
        field=float(self.inst.query('R7')[1:])
        if printer==True:
            print('current field is %5.4f T'%field)
        return field
    
    def setfield(self, target, printer=False):
        self.inst.write('$J%f'%target)
        self.inst.write('$A1')               #activate "GOTO SET"
        if printer==True:
            print('target field is %5.4f T'%target)

##############################################################################

    def turn_off(self, printer=False):
        self.goto(0)
    
        sleep(0.1)
        self.inst.write('$A0')     #hold operation
        sleep(0.1)
        self.inst.write('$H0')     #Heater off
        sleep(0.1)
        self.inst.write('$C2')     #remote & unlocked
        self.inst.close()          #close connection with magnet
        if printer==True:
            print('Connection to magnet closed!')
        
##############################################################################
    # goto field either with certain rate or with maximum rate
    
    def goto(self,target,rate='max', factor=1, printer=False):
        if rate=='max':
            self.goto_max(target, factor, printer)
        else:
            self.goto_set(target, rate, printer)
            
##############################################################################

            
    # goto certain field with certain rate (not recommended)
        # wait until magnet got close to certain field
        # approximate remaining time
    def goto_set(self, target, rate, printer=True):
        self.setrate(rate,printer)
        self.setfield(target,printer)
        check=False
        while check==False:
            field=self.readfield(printer)
            time=60*(abs(target-field)/rate)
            if np.abs(field-target)< 3e-4:
                if printer==True:
                    print('\nTarget Field reached...OK')
                check=True
                break
            else:
                if printer==True:
                    print('Field is %6.4f T, remaining time is %.1f s'%(field,time),end='\r')
                sleep(0.1)
                pass
        return field

##############################################################################

    # goto field with maximum allowed rate (recommended)
        # just need target B field as input
        # wait until magnet got close to certain field
        # approximate remaining time by polyfit (check appendix)
    
    def goto_max(self, target, factor=1, printer=True):
        # goto to defined B field with maximum speed
        
        # Scheer III magnet specific max rates, and slowdown
        spez={'rate':[0.723,0.2410,0.1205],'field':[7.8,9.6,12]}
        # fake spez for testing
        # spez={'rate':[0.7,0.6,0.5],'field':[.08,.1,0.12]}
        # reduce rate by factor to prenvent any quenching
        reduction=.9
        if factor>1:
            print('factor too high! Set to 1')
            factor=1
        redfactor=factor*reduction
        
        
        # Approximate time
        if printer==True:
            field=self.readfield(printer)
            # time approx parameter from polyfit
            a,b,c=5.71663,6.31138,12.3614
            approx=abs(a*np.log((target+b)/(field+b)*(c-field)/(c-target))*60)/redfactor
        
        # prevent magnetic fields, over max field (without lambda fridge)
        if target>spez['field'][2]:
            target=spez['field'][2]
            if printer==True:
                print('target field to high, set to %f T'%spez['field'][2])
        elif target<-spez['field'][2]:
            target=-spez['field'][2]
            if printer==True:
                print('target field to low, set to %f T'%(-spez['field'][2]))
            
        # Wait and adjust rate Loop
            # TODO adjust setfield to lower range
                #if target > spez[1]
                    #set target spez[1]
                #if target < spez[0]
                    #set target spez[0]
                #else
                    #set targetfield
        check=False
        while check==False:
            # get field
            field=self.readfield(printer)
            absfield=np.abs(field)
            
            # check if field is in range 
            if 0 <= absfield < spez['field'][0]:
                # set the rate to the corresponding range
                rate=spez['rate'][0]*redfactor
            
            # check if field is in range 
            elif spez['field'][0] <= absfield  <spez['field'][1]:
                # set the rate to the corresponding range
                rate=spez['rate'][1]*redfactor
            
            # check if field is in range     
            elif spez['field'][1] <= absfield <= spez['field'][2]:
                # set the rate to the corresponding range
                rate=spez['rate'][2]*redfactor
            
            # check if field is out of range (not gonna happen)    
            elif absfield>spez['field'][2]:
                # set rate to a lower than lowest rate
                rate=spez['rate'][2]*redfactor*.5
                target=0
                print('\nERROR: Field is too high!!!')
                
            self.setfield(target, printer)
            self.setrate(rate, printer)
            actual_rate=self.readrate(printer)
            
            
            if printer==True:
                time=abs(a*np.log((target+b)/(field+b)*(c-field)/(c-target))*60)/redfactor
                print('field %+07.4f/%+07.4f T, rate %05.4f, time %07.2f/%07.2f s'%(field,target,actual_rate,time,approx),
                      end='\r')
            if np.abs(field-target)< 1e-4:
                if printer==True:
                    print('\nTarget Field reached...OK')
                check=True
                break
            else:
                sleep(0.1)
                pass
        return field
    
        # for calculating time at scheer III
        # y=0.723,0.723,0.2410,0.1205
        # x=0,7.8,9.6,12
        # z=np.polyfit(x, y, 2)
        # p = np.poly1d(z)
        # xp = np.linspace(0, 12, 100)
        # plt.plot(x, y, '.', xp, p(xp), '-')
        # # integration with Wolfram alpha
        # # integrate 1/(-0.00936806*x**2+0.05667739*x+0.73087464 )
        # x = np.linspace(0, 12, 100)
        # y=5.71663*np.log(x+6.31138)-5.71663*np.log(12.3614-x)-5.71663*np.log(6.31138)+5.71663*np.log(12.3614)
        # plt.plot(x,y)

##############################################################################
##############################################################################

class AM430():
    def __init__(self, IP='192.168.1.103', printer=False):
        rm=pyvisa.ResourceManager('@py')
        inst=rm.open_resource('TCPIP::'+IP+'::7180::SOCKET',
                              read_termination='\r\n',
                              write_termination='\r\n')
        self.inst=inst
        inst.write_termination = u'\r\n'
        inst.read_termination = u'\r\n'
        inst.timeout=2000
        inst.chunk_size = 20480 #100kb
        
        fake_idn=self.inst.read()
        stupid=self.inst.read()
        if printer==True:
            print('fake id: %s, '%fake_idn)
            print('%s - well, fuck you too!'%stupid)
        
    def idn(self, printer=False):
        self.inst.write('*IDN?')
        idn=self.inst.read()
        if printer == True:
            print('id: %s, '%idn)
        return idn
        
    def exit(self):
        self.inst.close()     
        
    def goto_zero(self):
        self.inst.write('ZERO')
    
    def pause(self):
        self.inst.write('PAUSE')
        
    def local(self):
        self.inst.write('SYSTem:LOCal')
        
    def turn_off(self, printer=False):
        self.goto(0, printer=printer)
        self.inst.write('*RST')
        self.inst.write('SYSTem:LOCal')
        self.inst.query('*OPC?')
            
    def readfield(self,printer=False):
        field=self.inst.query('FIELD:MAGnet?')
        if printer==True:
            print('current field is %s T'%field)
        return float(field)
    
    def setfield(self, target, printer=False):
        self.inst.write('CONFigure:FIELD:TARGet %6.5f'%target)
        if printer==True:
            new_target=self.inst.query('FIELD:TARGet?')
            print('target field is %s T'%new_target)    
        
##############################################################################
    def reinitialize(self, printer=False):
        #self.inst.write('*RST')
        # Each 4th write should be interrupted with *OPC?
        self.inst.query('*OPC?')
        # remote mode
        #self.inst.write('SYSTem:REMote')
        # clear event register, probably not usable
        self.inst.write('*CLS')
        # units tesla/min
        self.inst.write('CONFigure:FIELD:UNITS 1') #T
        self.inst.write('CONFigure:RAMP:RATE:UNITS 1') #1/min
        self.inst.query('*OPC?')
        # calibration factor
        self.inst.write('CONFigure:COILconst 0.106500')
        # max current
        self.inst.write('CONFigure:CURRent:LIMit 65')
        # quench detect on 1, 0 off
        self.inst.write('CONFigure:QUench:DETect 0')
        self.inst.query('*OPC?')
        # set segments (target ramp)
        self.inst.write('CONFigure:RAMP:RATE:SEGments 2')
        self.inst.write('CONFigure:RAMP:RATE:FIELD 1,0.2106,5.325')
        self.inst.write('CONFigure:RAMP:RATE:FIELD 2,0.1053,7')
        self.inst.query('*OPC?')
        # set segments (external ramp down)
        self.inst.write('CONFigure:RAMPDown:RATE:SEGments 2')
        self.inst.write('CONFigure:RAMPDown:RATE:FIELD 1,0.2106,5.325')
        self.inst.write('CONFigure:RAMPDown:RATE:FIELD 2,0.1053,7')
        self.inst.query('*OPC?')
        # hold mode?
        self.inst.write('PAUSE')
        # heater on?
        if printer==True:
            print(self.inst.query('SYSTem:ERRor?'))
            Cc=self.inst.query('COILconst?')
            print('coil const (.1065 T/A) = %s'%Cc)
            fu=self.inst.query('FIELD:UNITS?')
            print('units (1|T) = %s'%fu)
            rru=self.inst.query('RAMP:RATE:UNITS?')
            print('units (1|pmin) = %s'%rru)
            cl=self.inst.query('CURRent:LIMit?')
            print('current limit (65 A) = %s'%cl)
            qd=self.inst.query('QUench:DETect?')
            print('quench detector (1 | on) = %s'%qd)
            rrs=self.inst.query('RAMP:RATE:SEGments?')
            print('ramp rate segments (2) = %s'%rrs)
            seg1=self.inst.query('RAMP:RATE:FIELD:1?')
            print('seg 1 (.2106T/min, 5.325T) = %s'%seg1)
            seg2=self.inst.query('RAMP:RATE:FIELD:2?')
            print('seg 2 (.1053T/min, 7T) = %s'%seg2)
            rrsd=self.inst.query('RAMPDown:RATE:SEGments?')
            print('ramp down rate segments (2) = %s'%rrsd)
            segd1=self.inst.query('RAMPDown:RATE:FIELD:1?')
            print('segd 1 (.2106T/min, 5.325T) = %s'%segd1)
            segd2=self.inst.query('RAMPDown:RATE:FIELD:2?')
            print('segd 2 (.1053T/min, 7T) = %s'%segd2)
            state=self.inst.query('STATE?')
            print('state (3 | paused)= %s'%state)
            rdn=self.inst.query('RAMPDown:COUNT?')
            print('external ramp downs: %s'%rdn)
            print('\n')

##############################################################################    
    def goto(self,target,rate='max', factor=1, printer=False):
        self.pause()
        if rate=='max':
            # set segments (target ramp)
            self.inst.write('CONFigure:RAMP:RATE:SEGments 2')
            self.inst.write('CONFigure:RAMP:RATE:FIELD 1,0.2106,5.325')
            self.inst.write('CONFigure:RAMP:RATE:FIELD 2,0.1053,7')
            self.inst.query('*OPC?')
            if factor==1:
                #do upper bracket
                factor=1
            if factor>1:
                print('Too High STUPID!!')
            if factor<1:
                print('Has to be implemented! MF! factor=1')
        else:
            # set segments (target ramp)
            self.inst.write('CONFigure:RAMP:RATE:SEGments 1')
            self.inst.write('CONFigure:RAMP:RATE:FIELD 1,%6.5f,7'%rate)
            self.inst.query('*OPC?')           
            
        if target==0:
            self.goto_zero()
        else:
            self.setfield(target, printer=printer)
            self.inst.write('RAMP')
        check=False
        while check==False:
            field=self.readfield(printer=False)
            if np.abs(field-target) < 1e-5:
                if printer==True:
                    print('%6.5f/%6.5f T'%(field,target),end='\r')
                    print('\nTarget Field reached...OK')
                check=True
                break
            else:
                if printer==True:
                    print('%6.5f/%6.5f T'%(field,target),end='\r')
                sleep(0.1)
                pass