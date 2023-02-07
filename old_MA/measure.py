import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from datetime import datetime
    
def plot_data(dataset=(np.zeros(3),
                       np.ones(120),
                       np.linspace(0,120),
                       np.linspace(0,-120),
                       np.linspace(0,120)*5),
              names=('Zeros','Ones','lin1','lin2','lin3'),
              style='test',
              filename='test',
              path='plots',
              show_plot=False,
              save_plot=True):
    '''plot_data(dataset), shows FIFO'''
    
    plt.style.use('driver\%s.mplstyle'%style)
    fig, axs = plt.subplots(int(np.shape(dataset)[0]),
                            sharex=True,
                            gridspec_kw={'hspace': 0})
    
    #adapt size
    size = fig.get_size_inches()
    size[1]=size[1]*np.shape(dataset)[0]/2
    fig.set_size_inches(size[0],size[1])
    
    for i, ds in enumerate(dataset):
        axs[i].plot(ds)
        axs[i].set_ylabel(names[i])
        axs[i].grid()
    
    # save plot
    if save_plot==True:
        # generates data path, if not made yet
        if not os.path.exists(path):
            os.makedirs(path)
        # generates name
        dt=datetime.today()
        date='%s'%(str(dt)[:-7].replace(':','-').replace(' ','_'))
        name='%s/%s_%s.pdf'%(path,filename,date)
        # save plot
        plt.savefig(name)
    
    if show_plot==False:
        plt.close('all')
        
def save_data(dataset=(np.zeros(3),np.ones(120)),
              names=('Zeros','Ones'),
              filename='test',
              path='data',
              printer=False,
              save_file=True):
    '''Save dataset as pandas.csv file, with timestamp'''
    # build dataframe
    df=[]
    for i, ds in enumerate(dataset):
        df.append(pd.DataFrame({names[i]:ds}))
    dataframe=pd.concat(df,axis=1)
    
    # print dataframe
    if printer==True:
        print('DataFrame looks like:')
        print(dataframe)
        
    # save data
    if save_file==True:
        # generates data path, if not made yet
        if not os.path.exists(path):
            os.makedirs(path)
        # generates name
        dt=datetime.today()
        date='%s'%(str(dt)[:-7].replace(':','-').replace(' ','_'))
        name='%s/%s_%s.csv'%(path,filename,date)
        # save to csv
        pd.DataFrame.to_csv(dataframe,name)
        # delete dataframe to prevent overflow
        del dataframe
        dataframe=False
    return dataframe

def norm_femto(x,amplification_factor=0):
    '''norms by amplification factor by femto [db]'''
    return x*10**(-amplification_factor/10)

def V_to_I(x,reference_resistance=240):
    '''Convert voltage to current, by reference_resistance [\Ohm]'''
    return x/reference_resistance
