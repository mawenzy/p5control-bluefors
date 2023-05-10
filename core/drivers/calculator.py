import logging
import time
import os

import numpy as np
from ADwin import ADwin
from threading import Lock
from time import sleep

from p5control.drivers.basedriver import BaseDriver
from p5control import DataGateway, InstrumentGateway

logger = logging.getLogger(__name__)

"""
Predefinition
"""

def calc_ptp(V, I):
    try:
        minV, maxV = np.min(V), np.max(V)
        minI, maxI = np.min(I), np.max(I)
        R_ptp = np.abs(maxV-minV) / np.abs(maxI-minI)
    except ValueError or RuntimeWarning:
        R_ptp = np.nan
    return R_ptp

def calc_rms(V, I):
    try:
        V_rms = np.sqrt(np.mean(np.abs(V)**2))
        I_rms = np.sqrt(np.mean(np.abs(I)**2))
        R_rms = V_rms / I_rms
    except ValueError or RuntimeWarning: 
        R_rms = np.nan
    return R_rms

def calc_lin(V, I):
    try:
        param = np.polyfit(V, I, 1)
        R, I_0 = 1/param[0], param[1]
        return R, I_0
    except TypeError:
        return np.nan, np.nan
        
def bin_y_over_x(x, y, bins):
    bins = np.append(bins, 2 * bins[-1] - bins[-2])
    _count, _ = np.histogram(x,
                            bins = bins,
                            weights=None)
    _count = np.array(_count, dtype='float64')
    _count[_count==0] = np.nan
    _sum, _ = np.histogram(x,
                    bins =bins,
                    weights=y)
    return _sum/_count

class Calculator(BaseDriver):
    """Represents an instrument which magically measures a sine wave. Both the frequency and the amplitude can be changed.

    Parameters
    ----------
    name : str
        name for this instance
    """

    def __init__(self, name: str):
        self._name = name
        self._delay_time = .1

        # all the names
        self._adwin = 'adwin'
        self._startstopname = 'startstop'

        self._temp = 'temp'
        self._offset = 'offsets'
        self._resistance_up = 'resistances_up'
        self._resistance_down = 'resistances_down'
        self._resistance_cv = 'resistances_cv'
        self._sweeps_up = 'sweeps_up'
        self._sweeps_down = 'sweeps_down'

        self.running = False
        self.step_size = 100
        self.bin_start = -.001
        self.bin_stop = .001
        self.bin_points = 101

    
    def get_status(self):
        return {
            "step_size": self.step_size,
            "running": self.running,
        }
    
    """
    Measurement
    """

    def _save_data(
        self,
        hdf5_path: str,
        array,
        dgw: DataGateway,
        **kwargs
    ):
        """Save data to hdf5 through a gateway. Overwrite this method if you want to change how or
        where this driver saves it data when being measured.
        
        Parameters
        ----------
        hdf5_path : str
            base hdf5_path under which you should save the data
        array
            data to save
        dgw : DataGateway
            gateway to the dataserver
        """
        if self.running:
            logger.debug('%s._save_data()', self._name)
            skipping = False
            path = f"{hdf5_path}/{self._name}/{self._startstopname}"
            save_path = f"{hdf5_path}/{self._name}/{self._temp}"

            try:
                startstop_len = dgw.get(path).shape[0]
            except KeyError:
                skipping = True
                
            try:
                calc_len = dgw.get(save_path).shape[0]
            except KeyError:
                calc_len = 0

            if not skipping:
                diff_len = startstop_len - calc_len
                if diff_len > 0:
                    for i in range(diff_len):
                        tic = time.time()
                        index = calc_len + i
                        slicer = slice(index, index+1, 1)
                        start = dgw.get_data(path, "start", slicer)[0]
                        stop =  dgw.get_data(path,  "stop", slicer)[0]
                        caser = dgw.get_data(path,  "case", slicer)[0]

                        if caser > 0:
                            self.calc_sweep(dgw, hdf5_path, start, stop, caser)
                        # if case == 0 / off
                        elif caser == 0:
                            self.calc_off(dgw, hdf5_path, start, stop)
                        # if case == -1 / cv
                        elif caser == -1:
                            self.calc_cv(dgw, hdf5_path, start, stop)
                        # if case < -1 / undefined
                        else:
                            raise ValueError('trigger state of adwin is undefined.')
                        toc = time.time()

                        array['time'] = tic
                        array['calc_time'] = toc-tic
                        array['start'] = start
                        array['stop'] = stop
                        array['case'] = caser
                        array['data_points'] = int((stop-start) / self.step_size)

                        dgw.append(save_path, array, **kwargs)
        else:
            sleep(self._delay_time)
                    
    def retrieve_data(
            self,
            dgw,
            hdf5_path,
            start,
            stop,
    ):
        path = f"{hdf5_path}/{self._adwin}"
        # data = dgw.get_data(path, indices=range(start, stop, self.step_size))
        # V1 = data["V1"]
        # V2 = data["V2"]
        # t1 = data["time"][0]
        # t2 = data["time"][-1]
        while True:
            try:
                V1 = dgw.get_data(path, indices=range(start, stop, self.step_size), field='V1')
                V2 = dgw.get_data(path, indices=range(start, stop, self.step_size), field='V2')
                t1 = dgw.get_data(path, indices=start, field='time')
                t2 = dgw.get_data(path, indices=stop,  field='time')

                t = ( t1 + t2 ) / 2
                return t, V1, V2
            except IndexError:
                sleep(.1)
    
    def calc_off(
            self,
            dgw,
            hdf5_path,
            start,
            stop,
    ):
        t, V1, V2 = self.retrieve_data(dgw,hdf5_path,start,stop)
        V1_off, V2_off = np.mean(V1), np.mean(V2)
        uV1_off, uV2_off = np.std(V1), np.std(V2)

        my_dict = {
            'time': t,
            'V1_off': V1_off,
            'V2_off': V2_off,
            'uV1_off': uV1_off,
            'uV2_off': uV2_off,
        }
        path = f"{hdf5_path}/{self._name}/{self._offset}"
        dgw.append(path, my_dict)

    def get_offsets(
            self, 
            dgw,
            hdf5_path
            ):
        logger.debug('%s.get_offsets()', self._name)
        try:
            path = f"{hdf5_path}/{self._name}/{self._offset}"
            data_off = dgw.get_data(path, indices=-2)
            V1_off = data_off['V1_off']
            V2_off = data_off['V2_off']
        except KeyError or IndexError:
            V1_off, V2_off = 0, 0
        return V1_off, V2_off
    
    # TODO
    def get_amplifications(self):
        logger.debug('%s.get_amplifications()', self._name)
        V1_amp = 100
        V2_amp = 100
        return V1_amp, V2_amp

    # TODO
    def get_resistance(self):
        return 47000

    def calc_cv(
            self,
            dgw,
            hdf5_path,
            start,
            stop,
    ):
        t, V1, V2 = self.retrieve_data(dgw, hdf5_path, start, stop)
        print(f"mean: {np.mean(V1)}, {np.mean(V2)}")
        
        V1_off, V2_off = self.get_offsets(dgw, hdf5_path)
        print(f"offset: {V1_off}, {V2_off}")
        V1_amp, V2_amp = self.get_amplifications()
        ref_R = self.get_resistance()
        
        print(f"V-offset: {np.mean(V1)-V1_off}, {np.mean(V2)-V2_off}")
        voltage = ( V1 - V1_off ) / V1_amp
        current = ( V2 - V2_off ) / V2_amp / ref_R
        print(f"voltage: {(np.mean(V1) - V1_off)}, current: {( np.mean(V2) - V2_off ) / ref_R}")

        mean_voltage = np.mean(voltage)
        mean_current = np.mean(current)
        print(f"voltage: {mean_voltage}, current: {mean_current}")
        std_voltage = np.std(voltage)
        std_current = np.std(current)
        R_mean = np.abs(mean_voltage/mean_current)
        
        uR_mean1 = np.abs(std_voltage / mean_current)
        uR_mean2 = np.abs(std_current * mean_voltage / mean_current**2)
        uR_mean = uR_mean1 + uR_mean2

        print(f"resistance: {R_mean} ({uR_mean})")
        my_dict = {
            'time': t,
            'R_mean': R_mean,
            'uR_mean': uR_mean
        }

        path = f"{hdf5_path}/{self._name}/{self._resistance_cv}"
        dgw.append(path, my_dict)


    def calc_sweep(
            self,
            dgw,
            hdf5_path,
            start,
            stop,
            caser,
    ):
        t, V1, V2 = self.retrieve_data(dgw,hdf5_path,start,stop)
        
        V1_off, V2_off = self.get_offsets(dgw, hdf5_path)
        V1_amp, V2_amp = self.get_amplifications()
        ref_R = self.get_resistance()
        
        voltage = ( V1 - V1_off ) / V1_amp
        current = ( V2 - V2_off ) / V2_amp / ref_R

        ## get R_ptp, R_rms, R_lin
        R_ptp = calc_ptp(voltage, current)
        R_rms = calc_rms(voltage, current)
        R_lin, I_o = calc_lin(voltage, current)

        my_dict = {
            'time': t,
            'R_ptp': R_ptp,
            'R_rms': R_rms,
            'R_lin': R_lin,
            'I_0': I_o,
        }


        # get binned voltage and currents
        ## get binned voltage
        bins = np.linspace(
            self.bin_start,
            self.bin_stop,
            int(self.bin_points),
            )
        bin_curr   = bin_y_over_x(voltage, current, bins)

        # save sweeps
        my_dict_sweep = {
                'time': t,
                'current': bin_curr
                }
                    
        # save data
        if caser%2 == 0:
            path = f"{hdf5_path}/{self._name}/{self._resistance_down}"
            path_sweep = f"{hdf5_path}/{self._name}/{self._sweeps_down}"
        if caser%2 == 1:
            path = f"{hdf5_path}/{self._name}/{self._resistance_up}"
            path_sweep = f"{hdf5_path}/{self._name}/{self._sweeps_up}"

        dgw.append(path, my_dict)
        dgw.append(
            path_sweep,
            my_dict_sweep,
            x_axis = 'V [V]',
            start = self.bin_start,
            stop = self.bin_stop,
            points = self.bin_points,
            plot_config = "lnspc",
            )


    """
    Overwrite
    """
    
    def open(self):
        pass

    def close(self):
        pass

    def stop_measuring(self):
        pass

    def setup_measuring(self):
        pass

    def start_measuring(self):
        pass

    def get_data(self):
        return {}
    
    def setRunning(self, value:bool):
        logger.debug('%s.setRunning()', self._name)
        self.running = value

    def getRunning(self):
        logger.debug('%s.getRunning()', self._name)
        return self.running
    
    def setStepSize(self, value:int):
        logger.debug('%s.setStepSize()', self._name)
        self.step_size = value

    def getStepSize(self):
        logger.debug('%s.getStepSize()', self._name)
        return self.step_size
    
    def setBinStart(self, value:float):
        logger.debug('%s.setBinStart()', self._name)
        self.bin_start = value

    def getBinStart(self):
        logger.debug('%s.getBinStart()', self._name)
        return self.bin_start
    
    def setBinStop(self, value:float):
        logger.debug('%s.setBinStop()', self._name)
        self.bin_stop = value

    def getBinStop(self):
        logger.debug('%s.getBinStop()', self._name)
        return self.bin_stop
        return self.bin_start
    
    def setBinPoints(self, value:int):
        logger.debug('%s.setBinPoints()', self._name)
        self.bin_points = value

    def getBinPoints(self):
        logger.debug('%s.getBinPoints()', self._name)
        return self.bin_points