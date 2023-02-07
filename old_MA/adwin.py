# -*- coding: utf-8 -*-
"""
Created on Fri Jun 26 15:06:25 2020

current Version 2.0 from 19.10.2020
Features:

    
@author: Oliver I.
Many Thanks to: Andreas Bloch

e.g.:
from driver.adwin import ADwin_gold
from time import sleep
adw=ADwin_gold()
adw.setup(average=10, sampling_rate=0, ranges=[1.25,10,1.25,10,1.25,1.25], printer=True)
adw.empty_data()
sleep(1)
I,V,dI,dV,T=adw.get_data()
adw.exit()

adw=ADwin_gold()
adw.setup(average=100, sampling_rate=0, ranges=[1.25,10,1.25,10,1.25,1.25], printer=True)
adw.realtime()
adw.exit()
"""
from driver.ADwin.ADwin import ADwin
from time import sleep
from datetime import datetime
import numpy as np
import json, os
import matplotlib.pyplot as plt
import matplotlib.animation as animation


    
class ADwin_gold():
    def __init__(self,process="ADwin_process"):
        '''Boots self written process.'''
        # initializing adwin
        self.adwin = ADwin()
        self.adwin.Boot("driver/ADwin/ADwin9.btl")
        self.adwin.Load_Process("driver/ADwin/%s.T91"%process)
        self.adwin.Start_Process(ProcessNo=1)
        
    def exit(self):
        '''Does nothing.'''
        # yes really nothing
        sleep(.1)
    
    def realtime_plot(self, sleeptime=.1):
        '''Show realtime channel input.'''
        #i=0
        print("Press Ctrl-C or stop to terminate.\n")
        plt.close('all')
        limit=20
        
        fig=plt.figure()
        ax=fig.add_subplot(1,1,1)
        xs=[]
        ys=[]
        def animate(i,xs,ys):
            
            count=self.get_count()
            data =self.get_FIFO(count)
            
            xs.append(datetime.now().strftime('%H:%M:%S.%f'))
            ys.append(np.mean(data[4]))
            
            #xs=xs[-limit:]
            #ys=ys[-limit:]
            ax.clear()
            ax.plot(xs,ys,'.')
            
            plt.xticks(rotation=45, ha='right')
            plt.subplots_adjust(bottom=.3)
            plt.title('test')
            plt.ylabel('ytest')
        
        
        ani=animation.FuncAnimation(fig, animate, fargs=(xs,ys),interval=200)
        plt.show()
        '''
        plt.grid()
        try:
            while i<20:
                self.empty_FIFO()
                sleep(sleeptime)
                i=i+1
                plt.clf()
                
            I=np.append(I,np.array(data[0], dtype='float64'),axis=0)
            V=np.append(V,np.array(data[1], dtype='float64'),axis=0)
            dI=np.append(dI,np.array(data[2], dtype='float64'),axis=0)
            dV=np.append(dV,np.array(data[3], dtype='float64'),axis=0)
                
                I=np.append(I,np.array(data[0], dtype='float64'),axis=0)
                V=np.append(V,np.array(data[1], dtype='float64'),axis=0)
                dI=np.append(dI,np.array(data[2], dtype='float64'),axis=0)
                dV=np.append(dV,np.array(data[3], dtype='float64'),axis=0)
                T=np.append(T,np.array(data[4], dtype='float64'),axis=0)
                
                
                
    
    
    
                #plt.plot(range(int(np.shape(I)[0])),I)
                #plt.plot(range(int(np.shape(V)[0])),V)
                #plt.plot(range(int(np.shape(dI)[0])),dI)
                #plt.plot(range(int(np.shape(dV)[0])),dV)
                #plt.plot(range(int(np.shape(T)[0])),T)
        except KeyboardInterrupt:
            pass'''
        
        
    def setup(self,
              average=100,
              sampling_rate=0,
              ranges=[10,10,10,10,10,10],
              printer=False,
              save_config=True):
        '''setup: sampling rate, or number of values,
                  but also ranges and conversion factors,
                  saves config file in addition'''

        # changing these values require more elaborated changes in process
        channels=[1,2,3,4,7,6]
        T_factor,T_off=.5,10
        spez1={10:1,5:2,2.5:4,1.25:8}
        spez2={1:0,2:1,4:2,8:3}
        ranges=np.array(ranges)
        factors, amplifier = np.zeros(len(ranges)), np.zeros(len(ranges))
        factors=ranges/32768

        # set either average or sampling rate
        sleep(1)
        if sampling_rate!=0:
            average=int(4e4/sampling_rate)
        self.adwin.Set_Par(Index=20, Value=average) #Set new Average Value
        self.adwin.Set_Par(Index=21, Value=0)       #Reset Loop
        sleep(1)
        actual_rate=self.adwin.Get_FPar(Index=20)

        # set preamplification and stuff
        for i in range(len(channels)):
            amplifier[i]=spez1[ranges[i]]
            pattern=spez2[amplifier[i]]

            # set musk pattern
            self.adwin.Set_Par(Index=channels[i],
                          Value=pattern)
            # set conversion factors
            self.adwin.Set_FPar(Index=channels[i]+30,
                          Value=factors[i])
            # set conversion offset
            self.adwin.Set_FPar(Index=channels[i]+40,
                          Value=ranges[i])

        # cosmetics and stuff    
        if printer==True or save_config==True:
            # builds config file
            date=str(datetime.now()) 
            config={'timestamp':date,
                    'average':average,
                    'sampling_rate':sampling_rate,
                    'actual_rate':actual_rate,
                    'channels':"'%s'"%str(channels),
                    'amplifier':"'%s'"%str(amplifier),
                    'ranges':"'%s'"%str(ranges),
                    'factors':"'%s'"%str(factors),
                    'T_factor':T_factor,
                    'T_off':T_off}

            if printer==True:
                print("average: %i"%config['average'])
                print("sampling_rate: %i"%config['sampling_rate'])
                print("actual_rate: %f"%config['actual_rate'])
                print("channels: %s"%config['channels'])
                print("amplifier: %s"%config['amplifier'])
                print("ranges: %s"%config['ranges'])
                print("factors: %s"%config['factors'])
                print("T_factor: %f"%config['T_factor'])
                print("T_off: %f"%config['T_off'])

            if save_config==True:
                # generates config path, if not made yet
                path='config'
                if not os.path.exists(path):
                    os.makedirs(path)
                # dumps config in file
                with open('config/ADwin_config.json','a+') as f:
                    json.dump(config,f,indent=1)
                    
    def realtime(self, sleeptime=.2):
        '''Show realtime channel input.'''
        progress=["|","/","-","\\"]
        i=0
        I,V,dI,dV=np.empty(0),np.empty(0),np.empty(0),np.empty(0)
        print("Press Ctrl-C or stop to terminate.\n")
        try:
            while True:
                self.empty_FIFO()
                sleep(sleeptime)
                count=self.get_count()
                data=self.get_FIFO(count)
                I,V=np.mean(data[0]),np.mean(data[1])
                dI, dV=np.mean(data[2]),np.mean(data[3])
                T=np.mean(data[4])
                print("%s (I=%05.2e, V=%05.2e, dI=%05.2e, dV=%05.2e [V]), T=%4.2f K    "
                      %(progress[i%4],I,V,dI,dV,T), end="\r")
                i=i+1
        except KeyboardInterrupt:
            pass
    
    def get_bandwidth(self):
        '''Get time, for new element in FIFO'''
        return 1/np.float(self.adwin.Get_FPar(Index=20))
        
    def get_data(self):
        '''Retrun I,V,dI,dV from FIFO.'''
        I=np.empty(0)
        count = self.get_count()
        sleep(self.get_bandwidth())
        count = np.ones(np.shape(count))*np.amax(count)
        data  = self.get_FIFO(count)
        I , V = np.array(data[0], dtype='float64'), np.array(data[1], dtype='float64')
        dI,dV = np.array(data[2], dtype='float64'), np.array(data[3], dtype='float64')
        T=np.array(data[4], dtype='float64')
        return I,V,dI,dV,T
    
    def get_FIFO(self,count=np.ones(5)*1e6):
        '''Reads FIFO'''
        data=[self.adwin.GetFifo_Float(FifoNo=1, Count=int(count[0])),
              self.adwin.GetFifo_Float(FifoNo=2, Count=int(count[1])),
              self.adwin.GetFifo_Float(FifoNo=3, Count=int(count[2])),
              self.adwin.GetFifo_Float(FifoNo=4, Count=int(count[3])),
              self.adwin.GetFifo_Float(FifoNo=7, Count=int(count[4]))]
        return data
    
    def empty_FIFO(self):
        '''Clears FIFO.'''
        self.adwin.Fifo_Clear(FifoNo=1)
        self.adwin.Fifo_Clear(FifoNo=2)
        self.adwin.Fifo_Clear(FifoNo=3)
        self.adwin.Fifo_Clear(FifoNo=4)
        self.adwin.Fifo_Clear(FifoNo=7)
        
    def get_count(self):
        '''Read how many values are in FIFO.'''
        count = [self.adwin.Fifo_Full(FifoNo=1),
                 self.adwin.Fifo_Full(FifoNo=2),
                 self.adwin.Fifo_Full(FifoNo=3),
                 self.adwin.Fifo_Full(FifoNo=4),
                 self.adwin.Fifo_Full(FifoNo=7)]
        return np.array(count)
    
    def get_empty(self):
        '''Read how many free spots in FIFO are left.'''
        empty = [self.adwin.Fifo_Empty(FifoNo=1),
                 self.adwin.Fifo_Empty(FifoNo=2),
                 self.adwin.Fifo_Empty(FifoNo=3),
                 self.adwin.Fifo_Empty(FifoNo=4),
                 self.adwin.Fifo_Empty(FifoNo=7)]
        return empty

# ADwin_process.bas
'''
#Define Buffersize 800000                ' Anzahl der Werte über die gemittelt wird (10^6 funktioniert nicht)

Dim Data_1[Buffersize] as Float as FIFO   ' Strom I über die Probe 
Dim Data_2[Buffersize] as Float as FIFO   ' Spannung U an der Probe
Dim Data_3[Buffersize] as Float as FIFO   ' differentieller Strom dI über die Probe
Dim Data_4[Buffersize] as Float as FIFO   ' differentielle Spannung dU an der Probe
Dim Data_7[Buffersize] as Float as FIFO   ' Temperatur [K] an der Probe

Dim c1, c2, c3, c4, c7, c6 as Long
Dim mp12, mp34, mp76 as Long
Dim count, mean as Long
Dim oldtime as Long

Init:

  c1 = 0
  c2 = 0
  c3 = 0
  c4 = 0
  c7 = 0
  c6 = 0
  
  Par_19  = 0     'aquire current mean value
  Par_20  = 100    'averaging factor
  Par_21  = 0     'time stamp
  oldtime = Par_21
  FPar_22  = 10 'temp offset
  FPar_23  = 0.5 'temp factor
  
  
  ' set verstärkung according Gold-HW p.50
  Par_1 = 00b
  Par_2 = 00b
  Par_3 = 00b
  Par_4 = 00b
  Par_7 = 00b
  Par_6 = 00b
    
  FPar_31 = 3.0517578125*10^-05
  FPar_32 = 3.0517578125*10^-05
  FPar_33 = 3.0517578125*10^-05
  FPar_34 = 3.0517578125*10^-05
  FPar_37 = 3.0517578125*10^-05
  FPar_36 = 3.0517578125*10^-05 
   
  FPar_41 = 10
  FPar_42 = 10
  FPar_43 = 10
  FPar_44 = 10
  FPar_47 = 10
  FPar_46 = 10
  
  FPar_19 = 0 'temperature
  FPar_20 = 0 'time stamp
  
  
  mp12 = (000000b | shift_left(Par_1, 6)) | shift_left(Par_2, 8)  ' Gold-HW p.55
  mp34 = (001001b | shift_left(Par_3, 6)) | shift_left(Par_4, 8)
  mp76 = (010011b | shift_left(Par_7, 6)) | shift_left(Par_6, 8)
  
  Set_Mux(mp12) ' needs 6.5us to be done 
  Sleep(65) ' waits 6.5us
  
EVENT:
  ' sets value over which it is averaged
  mean = Par_20
  mp12 = (000000b | shift_left(Par_1, 6)) | shift_left(Par_2, 8)  ' Gold-HW p.55
  mp34 = (001001b | shift_left(Par_3, 6)) | shift_left(Par_4, 8)
  mp76 = (010011b | shift_left(Par_7, 6)) | shift_left(Par_6, 8)
  
  If (Par_21 = mean) Then
    
    Data_1 = c1/mean*FPar_31-FPar_41 'Data_1 = c1/mean*38.147*10^-6-1.25
    Data_2 = c2/mean*FPar_32-FPar_42 'Data_2 = c2/mean*38.147*10^-6-1.25
    'Pro digit 305.175uV -10V Offset. Vgl. S.13 ADwin Gold Handbuch
    c1 = 0
    c2 = 0
    Data_3 = c3/mean*FPar_33-FPar_43 'Data_1 = c1/mean*38.147*10^-6-1.25
    Data_4 = c4/mean*FPar_34-FPar_44 'Data_2 = c2/mean*38.147*10^-6-1.25
    'Pro digit 305.175uV -10V Offset. Vgl. S.13 ADwin Gold Handbuch
    c3 = 0
    c4 = 0
    Data_7 = (c7/mean*FPar_37-FPar_47+FPar_22)*FPar_23 'Data_1 = c1/mean*38.147*10^-6-1.25
    c7 = 0 
    FPar_20 = 1/((Read_Timer() - oldtime + 27)* 25*10^-9) '8 offset durch 2 read befehle
    oldtime = Read_Timer()
    Par_21 = 0
  endif
  ' Par_19: Loop index
  ' Par_19 = Par_19+1
  Inc(Par_21)
  
  ' Start converting analog mux1/2 to digital Gold-HW p.57
  Start_Conv(11b)  ' needs 5us
  Set_Mux(mp34) 'Multiplexer auf Kanal 3 und 4 setzen
  Wait_EOC(11b) 'waits for start_conv, set_mux running in parallel
  c1 = c1 + ReadADC(1) 'Spannung am Referenzwiderstand
  c2 = c2 + ReadADC(2) 'Spannung an der Probe
  Sleep(15) ' waits additional 1.5us for musker to be finished
  
  ' Start converting analog mux 3/4 to digital
  Start_Conv(11b)
  Set_Mux(mp76) 'Multiplexer auf Kanal 7 setzen
  Wait_EOC(11b)
  c3 = c3 + ReadADC(1) 'Lock In Spannung am Referenzwiderstand
  c4 = c4 + ReadADC(2) 'Lock In Spannung an der Probe
  Sleep(15)
  'Par_13 = Data_3
  'Par_14 = Data_4
  
  Start_Conv(11b)
  Set_Mux(mp12) 'Multiplexer auf Kanal 1 und 2 setzen
  Wait_EOC(11b)
  c7 = c7 + ReadADC(1) 'Temperatur von LakeShore
  c6 = c6 + ReadADC(2) 'not used
  'Par_15 = Data_7[0]
  'Par_16 = Data_6
  Sleep(15)

'''