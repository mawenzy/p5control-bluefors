from p5control import DataGateway, InstrumentGateway
import numpy as np

from threading import Thread, Event
from queue import Queue, Empty

from time import sleep, time
from scipy.signal import savgol_filter as sg
from scipy.signal import find_peaks as fp
from scipy.optimize import curve_fit
from logging import getLogger
from qtpy.QtCore import QThread, QObject

import warnings
warnings.filterwarnings("error")
from scipy.optimize._optimize import OptimizeWarning

logger = getLogger(__name__)


def get_tmin_tmax(t, V, N, f):
    win_len = np.nanmax([int(N/f), 3])
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
        print(f'ERROR IN MIN MAX PEAKS, mins: {min_peaks}, maxs: {max_peaks}')
    return t[min_peaks], t[max_peaks]

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
    try:
        minV, maxV = np.min(V), np.max(V)
        minI, maxI = np.min(I), np.max(I)
        R_ptp = np.abs(maxV-minV)/np.abs(maxI-minI)
    except ValueError or RuntimeWarning:
        R_ptp = np.nan
    return R_ptp

def calc_rms(V, I):
    try:
        V_rms = np.sqrt(np.mean(np.abs(V)**2))
        I_rms = np.sqrt(np.mean(np.abs(I)**2))
        R_rms = V_rms/I_rms
    except ValueError or RuntimeWarning: 
        R_rms = np.nan
    return R_rms

def calc_lin(V, I):
    try:
        [R_lin, I_0_1, I_0_2], _ = curve_fit(combined_lin_fit, V, I)
    except OptimizeWarning or ValueError:
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


class SweeperWorker(Thread):
    """Sweeping tool Worker

    Parameters
    ----------
    name : str
        name for this instance
    _queue : Queue()
        put in queue to obtain calc refs
    """
    def __init__(
            self, 
            name, 
            _queue,
            _delay_time,
            _hdf5_path,
            _offset_name,
            _resistance_name,
            _sweeps_name
            ):
        super().__init__()
        self.daemon = True
        self.exit_request = Event()

        self._name = name
        self._queue = _queue
        
        self._delay_time = _delay_time
        self._hdf5_path = _hdf5_path
        self._offset_name = _offset_name
        self._resistance_name = _resistance_name
        self._sweeps_name = _sweeps_name

        self.open()

    def open(self):
        self.dgw = DataGateway()
        self.dgw.connect()
    
    def close(self):
        self.dgw.disconnect()

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

    def retrieve_offsets(self, m_path):
        path = f"{m_path}/{self._name}/{self._offset_name}"
        try:
            ind = int(self.dgw.get(path).shape[0])-1
            offsets = self.dgw.get_data(path, indices=slice(ind, None, None))
        except KeyError:
            offset_sample, offset_reference, offset_time = 0,0, np.nan
            logger.error(f"{self.name}.retrieve_offsets() no offsets found.")
        else:
            offset_sample = offsets['offset_sample'][0]
            offset_reference = offsets['offset_reference'][0]
            offset_time = offsets['time'][0]
        return offset_sample, offset_reference, offset_time

    """
    Calculations
    """
    def run(self):
        logger.debug(f"{self.name}_worker.run()")
        while not self.exit_request.is_set():
            try:
                calc_dict = self._queue.get(block=True, timeout=self._delay_time)
                logger.debug(f"{self._name}_worker, input: {calc_dict}")
            
                if calc_dict['key']=='offset':
                    # get data from dgw
                    _, ref_V = self._get_dataset(calc_dict['tic'], calc_dict['toc'], calc_dict['tic_ndx'][0], calc_dict['m_path'], multi_keyword='reference')
                    _, sample_V = self._get_dataset(calc_dict['tic'], calc_dict['toc'], calc_dict['tic_ndx'][1], calc_dict['m_path'], multi_keyword='sample')
                    _, source_V = self._get_dataset(calc_dict['tic'], calc_dict['toc'], calc_dict['tic_ndx'][2], calc_dict['m_path'], multi_keyword='source')

                    # get calculations done        
                    my_dict = {'time': calc_dict['tic'],
                            'offset_source': np.mean(source_V),
                            'offset_sample':np.mean(sample_V),
                            'offset_reference': np.mean(ref_V),
                            'std_source': np.std(source_V),
                            'std_sample': np.std(sample_V),
                            'std_reference': np.std(ref_V)
                            }

                    # save data
                    path = f"{calc_dict['m_path']}/{self._name}/{self._offset_name}"
                    self.dgw.append(
                        path,
                        my_dict,
                        offset_time = calc_dict['offset_time'],
                        max_current = calc_dict['max_current'],
                    )

                elif calc_dict['key']=='sweep':               
                    # get data from dgw
                    source_t, source_V = self._get_dataset(calc_dict['tic'], calc_dict['toc'], calc_dict['tic_ndx'][0], calc_dict['m_path'], multi_keyword='reference')
                    sample_t, sample_V = self._get_dataset(calc_dict['tic'], calc_dict['toc'], calc_dict['tic_ndx'][1], calc_dict['m_path'], multi_keyword='sample')
                    ref_t,       ref_V = self._get_dataset(calc_dict['tic'], calc_dict['toc'], calc_dict['tic_ndx'][2], calc_dict['m_path'], multi_keyword='source')

                    # get min und max peak indices
                    tmins, tmaxs = get_tmin_tmax(source_t, source_V, calc_dict['sweep_counts'], calc_dict['frequency'])

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
                    offset_sample, offset_reference, offset_time = self.retrieve_offsets(calc_dict['m_path'])

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
                        calc_dict['bin_start'], 
                        calc_dict['bin_stop'], 
                        int(calc_dict['bin_points'])
                        )

                    ## get binned currents
                    bin_curr_up   = bin_y_over_x(voltage_up, current_up, bin_volt)
                    bin_curr_down = bin_y_over_x(voltage_down, current_down, bin_volt)

                    # TODO Get dGs

                    # save sweeps
                    my_dict_sweep = {
                            'time': calc_dict['tic'],
                            'current_upsweep': bin_curr_up,
                            'current_downsweep': bin_curr_down,
                            'offset_time': offset_time,
                            }
                    
                    path = f"{calc_dict['m_path']}/{self._name}/{self._sweeps_name}"
                    self.dgw.append(
                        path, 
                        my_dict_sweep, 
                        x_axis = 'V [V]',
                        start = calc_dict['bin_start'],
                        stop = calc_dict['bin_stop'],
                        points = calc_dict['bin_points'],
                        max_current = calc_dict['max_current'],
                        amplitude = calc_dict['amplitude'],
                        frequency = calc_dict['frequency'],
                        sweep_counts = calc_dict['sweep_counts'],
                        plot_config = "lnspc"
                        )
                    
                    
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
                        'time': calc_dict['tic'],
                        'R_ptp': R_ptp,
                        'R_rms': R_rms,
                        'R_lin': R_lin,
                        'I_0_1': I_0_1,
                        'I_0_2': I_0_2,
                        'offset_time': offset_time,
                        }
                    path = f"{calc_dict['m_path']}/{self._name}/{self._resistance_name}"
                    self.dgw.append(
                        path,
                        my_dict_resistance,
                        start = calc_dict['bin_start'],
                        stop = calc_dict['bin_stop'],
                        points = calc_dict['bin_points'],
                        max_current = calc_dict['max_current'],
                        amplitude = calc_dict['amplitude'],
                        frequency = calc_dict['frequency'],
                        sweep_counts = calc_dict['sweep_counts'],
                    )

                else:
                    logger.error(f"{self.name}: wrong keyword, drop calculation.")
                self._queue.task_done()
            except Empty:
                continue
        self.close()
        logger.debug(f"{self.name}_worker.stopped()")


#########################################################################################################################
class Sweeper:
    """Sweeping tool

    Parameters
    ----------
    name : str
        name for this instance
    delay_time : float
        delay time for all operations, def: 0.1
    max_current : float
        max_current for power source, def: 0.1
    """
    def __init__(self, 
                 name: str = 'sweep',
                 delay_time: float = .1,
                 max_current: float = .1):

        self._queue = Queue()
        self._delay_time = delay_time
        self._max_current = max_current

        # Names
        self._name = name
        self._hdf5_path = "m000000"
        self._offset_name = "offsets"
        self._resistance_name = "resistances"
        self._sweeps_name = "sweeps"
        
        # Offset
        self._offset_time = 1   

        # Sweeps
        self._amplitude = .33
        self._frequency = 2.003
        self._sweep_counts = 10

        # Bins
        self._bin_start = -2e-3
        self._bin_stop = 2e-3
        self._bin_points = 101
        
        self.open()

    def open(self):
        self.gw = InstrumentGateway()
        self.dgw = DataGateway()
        self.worker = SweeperWorker(
            name = self._name,
            _queue = self._queue,
            _delay_time = self._delay_time,
            _hdf5_path = self._hdf5_path,
            _offset_name = self._offset_name,
            _resistance_name = self._resistance_name,
            _sweeps_name = self._sweeps_name,
            )

        self.gw.connect()
        self.dgw.connect()
        self.worker.exit_request.clear()
        self.worker.start()

        self.gw.source_bias.set_max_current(self._max_current)

        """Just logs the call to debug."""
        logger.debug(f'sweeps/offset.open()')   

    def close(self):
        while not self.worker.exit_request.is_set():
            self.worker.exit_request.set()
            sleep(.1)
        self.gw.disconnect()
        self.dgw.disconnect()
        logger.debug(f"{self._name}.close()")

    """
    Measurement
    """
    def get_offsets(self):
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

        calc_dict = {
            'key': 'offset',
            'm_path': m.path,
            'tic': tic,
            'toc': toc,
            'tic_ndx': tic_ndx,
            'offset_time': self._offset_time,
            '_delay_time': self._delay_time,
            'max_current': self._max_current,
        }
        
        self._queue.put(calc_dict)

        sleep(self._offset_time + self._delay_time)

        if stop_measurement:
            m.stop()

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
                # tic_ndx.append(int(np.max([0, ind-2*1000*self._delay_time])))
                tic_ndx.append(ind)
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
        m_time = self._sweep_counts / self._frequency + self._delay_time
        toc = tic + m_time

        calc_dict = {
            'key': 'sweep',
            'm_path': m.path,
            'tic': tic,
            'toc': toc,
            'tic_ndx': tic_ndx,
            'amplitude': self._amplitude,
            'frequency': self._frequency,
            'sweep_counts': self._sweep_counts,
            '_delay_time': self._delay_time,
            'max_current': self._max_current,
            'bin_start': self._bin_start,
            'bin_stop': self._bin_stop,
            'bin_points': self._bin_points,
        }
        
        self._queue.put(calc_dict)
        sleep(m_time)

        if stop_measurement:
            m.stop()
            