from p5control import DataGateway, InstrumentGateway
import numpy as np

from qtpy.QtCore import QThread

from time import sleep, time
from scipy.signal import savgol_filter as sg
from scipy.signal import find_peaks as fp
from scipy.optimize import curve_fit
from logging import getLogger

logger = getLogger(__name__)
class Sweeper:
    """Sweeping tool

    Parameters
    ----------
    name : str
        name for this instance
    """
    def __init__(self, 
                 name: str = 'sweep',
                 delay_time: float = .1):

        # Names
        self._name = name   
        self._hdf5_path = 'm000000'
        self._offset_name = "offsets"
        self._resistance_name = "resistances"
        self._sweeps_name = "sweeps"

        self._delay_time = delay_time
        self._max_current =.1

        self.open()
    
    def open(self):
        self.gw = InstrumentGateway()
        self.dgw = DataGateway()

        self.gw.connect()
        self.dgw.connect()

        """Just logs the call to debug."""
        logger.debug(f'sweeps/offset.open()')
    
    
    def _get_dataset(self, tic, toc, tic_ndx, path, multi_keyword):
        path = f"{path}/multi_{multi_keyword}/"
        while True:
            try:
                test = self.dgw.get_data(path, indices=slice(-1, None, None), field='time')[0]
                if test > toc:
                    break
            except KeyError:
                sleep(self._delay_time)

        multi = self.dgw.get_data(path, indices=slice(tic_ndx, None, None))
        time, V = multi['time'], multi['V']
        indices = (np.argmin(np.abs(time-tic)), 
                   np.argmin(np.abs(time-toc)))
        return time[indices[0]:indices[1]], V[indices[0]:indices[1]]


#######################################################################################
class Offsets(Sweeper):
    """Sweeping tool

    Parameters
    ----------
    name : str
        name for this instance
    """
    def __init__(self):
        super().__init__()

        # Offset
        self._offset_time = 1    

    """
    Measurement
    """
    def get_offset(self):
        # if there is no measurement, initiate one
        m = self.gw.measure()
        stop_measurement = False

        if not m.running:
            stop_measurement = True
            m.start()

        # setup bias_source amplitude to 0V output
        self.gw.source_bias.set_amplitude(0)

        # wait for measurement
        tic_ndx = []
        for s in ['reference', 'sample', 'source']:
            # if measurement just started, dataset doen't exist => Keyerror
            try:
                tic_ndx.append(int(self.dgw.get(f'{m.path}/multi_{s}').shape[0])-1)
            except KeyError:
                tic_ndx.append(0)

        sleep(self._delay_time)
        tic = time()
        toc = tic + self._offset_time

        # get data from dgw
        _, ref_V = self._get_dataset(tic, toc, tic_ndx[0], m.path, multi_keyword='reference')
        _, sample_V = self._get_dataset(tic, toc, tic_ndx[1], m.path, multi_keyword='sample')
        _, source_V = self._get_dataset(tic, toc, tic_ndx[2], m.path, multi_keyword='source')

        if stop_measurement:
            m.stop()

        # get calculations done        
        my_dict = {'time': tic,
                'offset_source': np.mean(source_V),
                'offset_sample':np.mean(sample_V),
                'offset_reference': np.mean(ref_V),
                'std_source': np.std(source_V),
                'std_sample': np.std(sample_V),
                'std_reference': np.std(ref_V)
                }

        # save data
        path = f"{m.path}/{self._name}/{self._offset_name}"
        self.dgw.append(
            path,
            my_dict,
            _delay_time = self._delay_time,
            offset_time = self._offset_time,
            max_current = self._max_current
        )

##########################################################################
"""
Pre-Definitions
"""

def get_min_max(t, tmins, tmaxs):
    mins, maxs = [], []
    for tmin in tmins:
        mins.append(np.argmin(np.abs(t-tmin)))
    for tmax in tmaxs:
        maxs.append(np.argmin(np.abs(t-tmax)))
    return mins, maxs

def get_up_down_sweeps(array, mins, maxs):
    up, down = np.array([]), np.array([])
    for i, max in enumerate(maxs):
        up = np.append(up, array[mins[i]:max])
        down = np.append(down, array[max:mins[i+1]])
    return up, down

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
      
def calc_ptp(V, I):
    minV, maxV = np.min(V), np.max(V)
    minI, maxI = np.min(I), np.max(I)
    return np.abs(maxV-minV)/np.abs(maxI-minI)

def calc_rms(V, I):
    V_rms = np.sqrt(np.nanmean(np.abs(V)**2))
    I_rms = np.sqrt(np.nanmean(np.abs(I)**2))
    return V_rms/I_rms

def calc_lin(V,I):
    try:
        [R_lin, I_0_1, I_0_2], _ = curve_fit(combined_lin_fit, V, I)
    except ValueError:
        [R_lin, I_0_1, I_0_2] = [np.nan, np.nan, np.nan]
    return R_lin, I_0_1, I_0_2
    
def combined_lin_fit(VV, R, I_0_1, I_0_2):
    # single data reference passed in, extract separate data
    # assumes biggest jump in voltage to be dividing index
    index = np.argmax(VV[:-1]-VV[1:])
    res1 = lin_fit_1(VV[:index], R, I_0_1, I_0_2)
    res2 = lin_fit_2(VV[index:], R, I_0_1, I_0_2)
    return np.append(res1, res2)

def lin_fit_1(V, R, I_0_1, I_0_2):
        return V / R + I_0_1

def lin_fit_2(V, R, I_0_1, I_0_2):
        return V / R + I_0_2


#########################################################################################################################
class Sweeps(Sweeper):
    def __init__(self):
        super().__init__()

        # Sweeps
        self._amplitude = .33
        self._frequency = 2.003
        self._sweep_counts = 10
        # Bins
        self._bin_start = -2e-3
        self._bin_stop = 2e-3
        self._bin_points = 401
    
    def run(self) -> None:
        self.get_sweeps()

    """
    Predefinition
    """

    def _get_tmin_tmax(self, t, V):
        win_len = np.nanmax([int(self._sweep_counts/self._frequency), 3])

        smooth_V = sg(V, window_length=win_len, polyorder=1)
        dV = np.gradient(smooth_V)
        smooth_dV = sg(dV, window_length=win_len, polyorder=1)
        ddV = np.gradient(smooth_dV)
        smooth_ddV = sg(ddV, window_length=win_len, polyorder=1)
        sym_ddV = smooth_ddV - np.mean(smooth_ddV)

        min_peaks = fp(sym_ddV, 
                        height=.25*np.nanmax(sym_ddV), 
                        distance=2*win_len)[0]
        max_peaks = fp(-sym_ddV,
                        height=.25*np.nanmax(sym_ddV),
                        distance=2*win_len)[0]

        while len(min_peaks) <= len(max_peaks):
            if min_peaks[0]>max_peaks[0]:
                min_peaks = np.append([0], min_peaks)
            else:
                min_peaks = np.append(min_peaks, [-1])
            print('ERROR IN MIN MAX PEAKS')
            print(min_peaks, max_peaks)
        return t[min_peaks], t[max_peaks]


    def get_offsets(self, m):
        path = f"{m.path}/{self._name}/{self._offset_name}"
        try:
            ind = int(self.dgw.get(path).shape[0])-1
            offsets = self.dgw.get_data(path, indices=slice(ind, None, None))
        except KeyError:
            offset_sample, offset_reference, offset_time = 0,0, np.nan
        else:
            offset_sample = offsets['offset_sample'][0]
            offset_reference = offsets['offset_reference'][0]
            offset_time = offsets['time'][0]
        return offset_sample, offset_reference, offset_time

    """
    Measurement
    """
    def get_sweeps(self):
        # if there is no measurement, initiate one
        m = self.gw.measure()
        stop_measurement = False

        if not m.running:
            stop_measurement = True
            m.start()

        # setup bias_source to sweep mode        
        self.gw.source_bias.set_amplitude(self._amplitude)
        self.gw.source_bias.set_frequency(self._frequency)
        self.gw.source_bias.set_sweep_count(self._sweep_counts)
        
        # wait for measurement
        tic_ndx = []
        multi_keywords = ['source', 'sample', 'reference']
        for s in multi_keywords:
            # if measurement just started, dataset doen't exist => Keyerror
            try:
                ind = int(self.dgw.get(f'{m.path}/multi_{s}').shape[0])
                tic_ndx.append(int(np.max([0, ind-2*1000*self._delay_time])))
            except KeyError:
                tic_ndx.append(0)
        
        # wait for source to be ready
        pre_tic = time()
        try:
            while self.dgw.get_data(f'{m.path}/multi_source', indices=-1, field='time') < pre_tic:
                sleep(self._delay_time)       
        except KeyError:
            sleep(1)
        
        self.gw.source_bias.trigger()
        tic = time()
        toc = tic + self._sweep_counts / self._frequency + self._delay_time

        # get data from dgw
        source_t, source_V = self._get_dataset(tic, toc, tic_ndx[0], m.path, multi_keyword=multi_keywords[0])
        sample_t, sample_V = self._get_dataset(tic, toc, tic_ndx[1], m.path, multi_keyword=multi_keywords[1])
        ref_t,       ref_V = self._get_dataset(tic, toc, tic_ndx[2], m.path, multi_keyword=multi_keywords[2])

        if stop_measurement:
            m.stop()

        # get min und max peak indices
        tmins, tmaxs = self._get_tmin_tmax(source_t, source_V)

        ## get binned t
        bint = np.linspace(
            np.min([
                np.nanmin(source_t), 
                np.nanmin(sample_t), 
                np.nanmin(ref_t)
                ]),
            np.max([
                np.nanmax(source_t), 
                np.nanmax(sample_t), 
                np.nanmax(ref_t)
                ]),
            int(np.mean([
                np.shape(source_t)[0],
                np.shape(sample_t)[0],
                 np.shape(ref_t)[0]
                 ])/10)
        )

        ## get binned sample_V and ref_V 
        sample_binV = bin_y_over_x(sample_t, sample_V, bint)
        ref_binV    = bin_y_over_x(   ref_t,    ref_V, bint)

        # get Offsets
        offset_sample, offset_reference, offset_time = self.get_offsets(m)

        # TODO: Get Amps and reference resistance
        amplification_sample = 1000
        amplification_reference = 1000
        reference_resistance = 47000

        # get current and voltage
        voltage = ( sample_binV - offset_sample ) / amplification_sample
        current = ( ref_binV - offset_reference ) / amplification_reference / reference_resistance

        # get up and down sweeps
        mins, maxs = get_min_max(bint, tmins, tmaxs)
        voltage_up, voltage_down = get_up_down_sweeps(voltage, mins, maxs)
        current_up, current_down = get_up_down_sweeps(current, mins, maxs)  

        # get binned voltage and currents
        ## get binned voltage
        bin_volt = np.linspace(
            self._bin_start, 
            self._bin_stop,
            int(self._bin_points)
            )

        ## get binned currents
        bin_curr_up   = bin_y_over_x(voltage_up, current_up, bin_volt)
        bin_curr_down = bin_y_over_x(voltage_down, current_down, bin_volt)

        # TODO Get dGs

        # save sweeps
        my_dict_sweep = {
                'time': tic,
                'current_upsweep': bin_curr_up,
                'current_downsweep': bin_curr_down,
                }
        
        path = f"{m.path}/{self._name}/{self._sweeps_name}"
        self.dgw.append(path, 
                    my_dict_sweep, 
                    x_axis = 'V [V]',
                    start = self._bin_start,
                    stop = self._bin_stop,
                    points = self._bin_points,
                    delay_time = self._delay_time,
                    amplitude = self._amplitude,
                    frequency = self._frequency,
                    sweep_counts = self._sweep_counts,
                    max_current = self._max_current,
                    plot_config = "lnspc")
        
        # get resistances
        ## remove nan's
        _logic_C_up = ~np.isnan(bin_curr_up)
        bin_volt_up_nnan = bin_volt[_logic_C_up]
        bin_curr_up_nnan = bin_curr_up[_logic_C_up]

        _logic_C_down = ~np.isnan(bin_curr_down)
        bin_volt_down_nnan = bin_volt[_logic_C_down]
        bin_curr_down_nnan = bin_curr_down[_logic_C_down]

        volt_nann = np.append(bin_volt_up_nnan, bin_volt_down_nnan)
        curr_nann = np.append(bin_curr_up_nnan, bin_curr_down_nnan)

        ## get R_ptp, R_rms, R_lin
        R_ptp = calc_ptp(volt_nann, curr_nann)
        R_rms = calc_rms(volt_nann, curr_nann)
        R_lin, I_0_1, I_0_2 = calc_lin(volt_nann, curr_nann)

        # save resistances   
        my_dict_resistance = {
            'time': tic,
            'R_ptp': R_ptp,
            'R_rms': R_rms,
            'R_lin': R_lin,
            'I_0_1': I_0_1,
            'I_0_2': I_0_2,
            'offset_time': offset_time,
            }

        path = f"{m.path}/{self._name}/{self._resistance_name}"
        self.dgw.append(
            path,
            my_dict_resistance,
            delay_time = self._delay_time,
            max_current = self._max_current,
            amplitude = self._amplitude,
            frequency = self._frequency,
            sweep_counts = self._sweep_counts,
            bin_start = self._bin_start,
            bin_stop = self._bin_stop,
            bin_points = self._bin_points,
        )

"""
# get resistances
        ## exclude gap data
        _logic_bin = (np.abs(bin_volt) <= self._excl_volt)

        bin_volt_excl = np.copy(bin_volt)
        bin_volt_excl[_logic_bin] = np.nan

        bin_curr_up_excl = np.copy(bin_curr_up)
        bin_curr_up_excl[_logic_bin] = np.nan

        bin_curr_down_excl = np.copy(bin_curr_down)
        bin_curr_down_excl[_logic_bin] = np.nan

        ## get from min and max
        min_bin_volt_excl = np.nanmin(bin_volt_excl)
        max_bin_volt_excl = np.nanmax(bin_volt_excl)

        min_bin_curr_excl = np.nanmin([np.nanmin(bin_curr_up_excl),
                                       np.nanmin(bin_curr_down_excl)])

        max_bin_curr_excl = np.nanmax([np.nanmax(bin_curr_up_excl),
                                       np.nanmax(bin_curr_down_excl)])

        R_max = np.abs( max_bin_volt_excl - min_bin_volt_excl ) / np.abs(
                max_bin_curr_excl - min_bin_curr_excl )

        ## get from rms
        rms_bin_volt_excl = calc_rms(bin_volt_excl)
        rms_bin_curr_excl = calc_rms(np.append(bin_curr_up_excl, bin_curr_down_excl))
        R_rms = rms_bin_volt_excl / rms_bin_curr_excl

        ## get from lin fit
        ### remove nans
        _logic = ~np.isnan(bin_volt_excl)
        bin_volt_excl_xnan = bin_volt_excl[_logic]
        bin_curr_up_excl_xnan = bin_curr_up_excl[_logic]
        bin_curr_down_excl_xnan = bin_curr_down_excl[_logic]

        _logic_C_up = ~np.isnan(bin_curr_up_excl_xnan)
        bin_volt_up_excl_xnan = bin_volt_excl_xnan[_logic_C_up]
        bin_curr_up_excl_xnan = bin_curr_up_excl_xnan[_logic_C_up]

        _logic_C_down = ~np.isnan(bin_curr_down_excl_xnan)
        bin_volt_down_excl_xnan = bin_volt_excl_xnan[_logic_C_down]
        bin_curr_down_excl_xnan = bin_curr_down_excl_xnan[_logic_C_down]

        ### get R from combined fit
        try:
            [R_lin, I_0_1, I_0_2], _ = curve_fit(combined_lin_fit, 
                                                np.append(bin_volt_up_excl_xnan,
                                                        bin_volt_down_excl_xnan),
                                                np.append(bin_curr_up_excl_xnan,
                                                        bin_curr_down_excl_xnan))
        except ValueError:
            [R_lin, I_0_1, I_0_2] = [np.nan, np.nan, np.nan]

        # save resistances   
        my_dict_resistance = {'time': tic,
                            'R_max': R_max,
                            'R_rms': R_rms,
                            'R_lin': R_lin,
                            'I_0_1': I_0_1,
                            'I_0_2': I_0_2,
                            }

        path = f"{self._hdf5_path}/{self._name}/{self._resistance_name}"
        self.dgw.append(
            path,
            my_dict_resistance,
            delay_time = self._delay_time,
            amplitude = self._amplitude,
            frequency = self._frequency,
            sweep_counts = self._sweep_counts,
            max_current = self._max_current,
            exclusion_voltage = self._excl_volt,
            bin_start = self._bin_start,
            bin_stop = self._bin_stop,
            bin_points = self._bin_points,
        )
"""
        