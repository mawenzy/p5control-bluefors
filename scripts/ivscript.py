from p5control import InstrumentServer, InstrumentGateway, DataGateway
from p5control.server.inserv import InstrumentServerError

from time import sleep
import numpy as np
from tqdm import tqdm

from core import ADwinGold2_v4, FemtoDLPVA100B, Keysight34461A_thermometer, AMI430, BlueForsAPI, Faulhaber, ZNB40, Rref

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='bluefors_server_script.log',
    level=logging.DEBUG,
    filemode='w', # overwrites logs every time this script is started
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(thread)6d %(name)-30s %(funcName)-20s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

class BlueforsServer():
    def __init__(self):
        pass
    def start_server(
            self, 
            server_name = None,
            S = '22',
            ):
        
        
        if server_name is None:
            self.inserv = InstrumentServer()
        else:
            self.inserv = InstrumentServer(data_server_filename=server_name)

        """
        Add Devices
        """
        self.inserv._add('adwin', ADwinGold2_v4)
        self.inserv._add('femtos', FemtoDLPVA100B)
        self.inserv._add('R_ref', Rref, R_ref = 53000)

        self.inserv._add('bluefors', BlueForsAPI)
        self.inserv._add('motor', Faulhaber)
        self.inserv._add('magnet', AMI430, '192.168.1.103')
        self.inserv._add('thermo', Keysight34461A_thermometer, 'TCPIP0::192.168.1.111::INSTR')
        self.inserv._add('vna', ZNB40, '192.168.1.104', case = 'time', S = S) # antenna=11, stripline=22
        
        self.inserv.start()  

    def stop_server(self):        
        self.inserv.stop()
        self.inserv._remove('femtos')
        self.inserv._remove('motor')
        self.inserv._remove('magnet')
        self.inserv._remove('vna')


class MeasurementScript():
    
    # vna_frequency in GHz
    # vna_power in dBm
    # magnetic_field in mT

    def __init__(self):        
        self.gw = InstrumentGateway()
        self.gw.connect()

        self.dgw = DataGateway()
        self.dgw.connect()
        
        self.offset_name = 'offset'
        self.sweep_name = 'sweep'
        self.magnetic_field_name = 'magnetic fields'
        self.vna_frequencies_name = 'vna frequencies'
        self.vna_powers_name = 'vna powers'
        self.vna_amplitude_name = 'vna amplitudes'
        self.iv_name = 'single IV'
        self.time_name = 'time evolution'
    
        self.adwin_average = 50
        self.femto1_amp = 1
        self.femto2_amp = 1
        self.magnet_rate = 0
        self.ramp_cool_down = 600
        self.meas_cool_down = 3
        self.meas_delay_time = .5

        self.amplitude = 0
        self.period = 28.0327 # equals 35.673mHz, 50Hz equals 20 ms
        self.sweep_time = 30
        self.offset_time = 3
        
        self.position_name = 'positions'
        self.voltage = 0.002 # V
        self.save_amp = .5
        self.motor_speed = 20

        self.initialize_devices()
    
    def initialize_devices(self):    
        self.gw.magnet.set_rate(self.magnet_rate)  
        self.gw.vna.setOutput(False) 
        
        self.gw.adwin.setAveraging(self.adwin_average)
        self.gw.adwin.setSweeping(False)
        self.gw.adwin.setOutput(False)
        
        # Abort Lockin Stuff
        self.gw.adwin.setLocking(False)
        self.gw.adwin.setLockinAmplitude(0)
        self.gw.adwin.setLockinFrequency(73.3)
        
    def save_state(self):
        self.gw.magnet.set_rate(0)  
        self.gw.magnet.goto_zero() 

        self.gw.vna.setOutput(False)

        self.gw.adwin.setAmplitude(0)
        self.gw.adwin.setSweeping(False)
        self.gw.adwin.setOutput(False)
    
    def measure_IV(self, name, amplitude, period, offset_time, sweep_time):        
        if amplitude is None:
            amplitude = self.amplitude      
        if period is None:
            period = self.period            
        if offset_time is None:
            offset_time = self.offset_time
        if sweep_time is None:
            sweep_time = self.sweep_time

        # measure offset  
        self.gw.adwin.setSweeping(False)
        self.gw.adwin.setOutput(False)
        m = self.gw.measure(f"{name}/{self.offset_name}")
        sleep(self.meas_delay_time)
        m.start()
        sleep(offset_time)
        m.stop()

        # measure sweep
        self.gw.adwin.setAmplitude(amplitude)
        self.gw.adwin.setPeriod(period)
        m = self.gw.measure(f"{name}/{self.sweep_name}")
        sleep(self.meas_delay_time)
        m.start()
        self.gw.adwin.setSweeping(True)
        self.gw.adwin.setOutput(True)
        sleep(sweep_time)
        m.stop()

    def single_IV(
            self,
            amplitude = None,
            period = None,
            sweep_time = None,
            femto1_amp = None,
            femto2_amp = None,
            offset_time = None,
            iv_name = None,
            ramp_cool_down = None,
            meas_cool_down = None,
            magnetic_field = None,
            vna_power = None,
            vna_frequency = None,            
                    ):
        if femto1_amp is None:
            femto1_amp = self.femto1_amp        
        if femto2_amp is None:
            femto2_amp = self.femto2_amp  
        if ramp_cool_down is None:
            ramp_cool_down = self.ramp_cool_down
        if meas_cool_down is None:
            meas_cool_down = self.meas_cool_down
        if iv_name is None:
            iv_name = self.iv_name

        # setup general stuff
        self.gw.adwin.setAveraging(self.adwin_average)
        self.gw.femtos.set_amplification_A(femto1_amp)
        self.gw.femtos.set_amplification_B(femto2_amp)
        self.gw.magnet.set_rate(self.magnet_rate)

        # setup magnet
        if magnetic_field is not None:
            self.gw.magnet.set_target_field(magnetic_field*1e-3) # magnet takes T
            self.gw.magnet.ramp()
            sleep(ramp_cool_down)      
        else:
            self.gw.magnet.goto_zero()
            magnetic_field = 0

        # setup VNA
        if vna_power is not None and vna_frequency is not None:
            self.gw.vna.setPower(vna_power)
            self.gw.vna.setTSweepFrequency(vna_frequency*1e9) # vna takes Hz
            self.gw.vna.setOutput(True)
        else:
            vna_frequency, vna_power = np.nan, np.nan   

        iv_name = f"{iv_name}_{magnetic_field:+.2f}mT_{vna_frequency:.3f}GHz_{vna_power:+.2f}dBm"  

        # do IV sweep
        self.measure_IV(
            iv_name, 
            amplitude=amplitude, 
            period=period, 
            offset_time=offset_time, 
            sweep_time=sweep_time
            )

    def magnetic_field_study(
            self,
            magnetic_fields,
            amplitude = None,
            period = None,
            sweep_time = None,
            femto1_amp = None,
            femto2_amp = None,
            offset_time = None,
            magnetic_field_name = None,
            ramp_cool_down = None,
            meas_cool_down = None,
            vna_power = None,
            vna_frequency = None,
                             ):
                
        if femto1_amp is None:
            femto1_amp = self.femto1_amp        
        if femto2_amp is None:
            femto2_amp = self.femto2_amp  
        if magnetic_field_name is None:
            magnetic_field_name = self.magnetic_field_name
        if ramp_cool_down is None:
            ramp_cool_down = self.ramp_cool_down
        if meas_cool_down is None:
            meas_cool_down = self.meas_cool_down

        # try:
        # setup general stuff
        self.gw.adwin.setAveraging(self.adwin_average)
        self.gw.femtos.set_amplification_A(femto1_amp)
        self.gw.femtos.set_amplification_B(femto2_amp)
        self.gw.magnet.set_rate(self.magnet_rate)

        # setup VNA
        if vna_power is not None and vna_frequency is not None:
            self.gw.vna.setPower(vna_power)
            self.gw.vna.setTSweepFrequency(vna_frequency*1e9) # vna takes Hz
            self.gw.vna.setOutput(True)
        else:
            vna_frequency, vna_power = np.nan, np.nan   

        magnetic_field_name = f"{magnetic_field_name}_{vna_frequency:.3f}GHz_{vna_power:+.2f}dBm"        

        # do IV sweep
        name = f"{magnetic_field_name}/no_field"
        self.measure_IV(
            name, 
            amplitude=amplitude, 
            period=period, 
            offset_time=offset_time, 
            sweep_time=sweep_time
            )

        # ramp to field, while adwin in savestate
        self.gw.adwin.setOutput(False)
        self.gw.adwin.setSweeping(False)
        self.gw.adwin.setAmplitude(0)
        self.gw.magnet.set_target_field(magnetic_fields[0]*1e-3) # magnet takes T
        self.gw.magnet.ramp()
        sleep(ramp_cool_down)
        
        for i, magnetic_field in enumerate(tqdm(magnetic_fields)):
            fname = f'uH={magnetic_field:+.2f}mT'
            
            # ramp to field, while adwin in savestate
            self.gw.adwin.setOutput(False)
            self.gw.adwin.setSweeping(False)
            self.gw.adwin.setAmplitude(0)
            self.gw.magnet.set_target_field(magnetic_field*1e-3) # magnet takes T
            self.gw.magnet.ramp()
            sleep(meas_cool_down) 

            # do IV sweep
            name = f"{magnetic_field_name}/{fname}"
            self.measure_IV(
                name, 
                amplitude=amplitude, 
                period=period, 
                offset_time=offset_time, 
                sweep_time=sweep_time
                )

        self.save_state()
        
    def frequency_study(
            self,
            vna_frequencies,
            vna_power,
            amplitude = None,
            period = None,
            sweep_time = None,
            femto1_amp = None,
            femto2_amp = None,
            offset_time = None,
            vna_frequencies_name = None,
            ramp_cool_down = None,
            meas_cool_down = None,
            magnetic_field = None,
                             ):
                
        if femto1_amp is None:
            femto1_amp = self.femto1_amp        
        if femto2_amp is None:
            femto2_amp = self.femto2_amp  
        if vna_frequencies_name is None:
            vna_frequencies_name = self.vna_frequencies_name
        if ramp_cool_down is None:
            ramp_cool_down = self.ramp_cool_down
        if meas_cool_down is None:
            meas_cool_down = self.meas_cool_down

        # setup general stuff
        self.gw.adwin.setAveraging(self.adwin_average)
        self.gw.femtos.set_amplification_A(femto1_amp)
        self.gw.femtos.set_amplification_B(femto2_amp)
        self.gw.magnet.set_rate(self.magnet_rate)

        # ramp to field, while adwin in savestate
        self.gw.adwin.setOutput(False)
        self.gw.adwin.setSweeping(False)
        self.gw.adwin.setAmplitude(0)
        if magnetic_field is not None:
            self.gw.magnet.set_target_field(magnetic_field*1e-3) # magnet takes T
            self.gw.magnet.ramp()
            sleep(ramp_cool_down)      
        else:
            self.gw.magnet.goto_zero()
            magnetic_field = 0

        vna_frequencies_name = f"{vna_frequencies_name}_{vna_power:+.2f}dBm_{magnetic_field:+.2f}mT"
            
        # do IV sweep
        name = f"{vna_frequencies_name}/no_frequency"
        self.measure_IV(
            name, 
            amplitude=amplitude, 
            period=period, 
            offset_time=offset_time, 
            sweep_time=sweep_time
            )
        
        for i, frequency in enumerate(tqdm(vna_frequencies)):
            fname = f'nu={frequency:.3f}GHz'
            
            # setup vna
            self.gw.vna.setPower(vna_power)
            self.gw.vna.setTSweepFrequency(frequency*1e9) # vna takes Hz
            self.gw.vna.setOutput(True)
            sleep(meas_cool_down) 

            name = f"{vna_frequencies_name}/{fname}"
            self.measure_IV(
                name, 
                amplitude=amplitude, 
                period=period, 
                offset_time=offset_time, 
                sweep_time=sweep_time
                )
                
        self.save_state()

    def power_study(
            self,
            vna_powers,
            vna_frequency,
            amplitude = None,
            period = None,
            sweep_time = None,
            femto1_amp = None,
            femto2_amp = None,
            offset_time = None,
            vna_powers_name = None,
            ramp_cool_down = None,
            meas_cool_down = None,
            magnetic_field = None,
                             ):
                
        if femto1_amp is None:
            femto1_amp = self.femto1_amp        
        if femto2_amp is None:
            femto2_amp = self.femto2_amp  
        if vna_powers_name is None:
            vna_powers_name = self.vna_powers_name
        if ramp_cool_down is None:
            ramp_cool_down = self.ramp_cool_down
        if meas_cool_down is None:
            meas_cool_down = self.meas_cool_down

        # setup general stuff
        self.gw.adwin.setAveraging(self.adwin_average)
        self.gw.femtos.set_amplification_A(femto1_amp)
        self.gw.femtos.set_amplification_B(femto2_amp)
        self.gw.magnet.set_rate(self.magnet_rate)

        # ramp to field, while adwin in savestate
        self.gw.adwin.setOutput(False)
        self.gw.adwin.setSweeping(False)
        self.gw.adwin.setAmplitude(0)
        if magnetic_field is not None:
            self.gw.magnet.set_target_field(magnetic_field*1e-3) # magnet takes T
            self.gw.magnet.ramp()
            sleep(ramp_cool_down)      
        else:
            self.gw.magnet.goto_zero()
            magnetic_field = 0

        vna_powers_name = f"{vna_powers_name}_{vna_frequency:.3f}GHz_{magnetic_field:+.2f}mT"
            
        # do IV sweep
        name = f"{vna_powers_name}/no_power"
        self.measure_IV(
            name, 
            amplitude=amplitude, 
            period=period, 
            offset_time=offset_time, 
            sweep_time=sweep_time
            )
        
        for i, vna_power in enumerate(tqdm(vna_powers)):
            fname = f'P={vna_power:+.2f}dBm'
            
            # setup vna
            self.gw.vna.setPower(vna_power)
            self.gw.vna.setTSweepFrequency(vna_frequency*1e9) # vna takes Hz
            self.gw.vna.setOutput(True)
            sleep(meas_cool_down) 

            name = f"{vna_powers_name}/{fname}"
            self.measure_IV(
                name, 
                amplitude=amplitude, 
                period=period, 
                offset_time=offset_time, 
                sweep_time=sweep_time
                )
                
        self.save_state()

    def amplitude_study(
            self,
            vna_amplitudes,
            vna_frequency,
            amplitude = None,
            period = None,
            sweep_time = None,
            femto1_amp = None,
            femto2_amp = None,
            offset_time = None,
            vna_amplitude_name = None,
            ramp_cool_down = None,
            meas_cool_down = None,
            magnetic_field = None,
                             ):
                
        if femto1_amp is None:
            femto1_amp = self.femto1_amp        
        if femto2_amp is None:
            femto2_amp = self.femto2_amp  
        if vna_amplitude_name is None:
            vna_amplitude_name = self.vna_amplitude_name
        if ramp_cool_down is None:
            ramp_cool_down = self.ramp_cool_down
        if meas_cool_down is None:
            meas_cool_down = self.meas_cool_down

        # setup general stuff
        self.gw.adwin.setAveraging(self.adwin_average)
        self.gw.femtos.set_amplification_A(femto1_amp)
        self.gw.femtos.set_amplification_B(femto2_amp)
        self.gw.magnet.set_rate(self.magnet_rate)

        # ramp to field, while adwin in savestate
        self.gw.adwin.setOutput(False)
        self.gw.adwin.setSweeping(False)
        self.gw.adwin.setAmplitude(0)
        if magnetic_field is not None:
            self.gw.magnet.set_target_field(magnetic_field*1e-3) # magnet takes T
            self.gw.magnet.ramp()
            sleep(ramp_cool_down)      
        else:
            self.gw.magnet.goto_zero()
            magnetic_field = 0

        vna_amplitude_name = f"{vna_amplitude_name}_{vna_frequency:.3f}GHz_{magnetic_field:+.2f}mT"
            
        # do IV sweep
        name = f"{vna_amplitude_name}/no_amplitude"
        self.measure_IV(
            name, 
            amplitude=amplitude, 
            period=period, 
            offset_time=offset_time, 
            sweep_time=sweep_time
            )
        
        for i, vna_amplitude in enumerate(tqdm(vna_amplitudes)):
            fname = f'V={vna_amplitude:+.3f}V'
            
            # setup vna
            self.gw.vna.setPower(20*np.log10(vna_amplitude/np.sqrt(2*50/1000)))
            self.gw.vna.setTSweepFrequency(vna_frequency*1e9) # vna takes Hz
            self.gw.vna.setOutput(True)
            sleep(meas_cool_down) 

            name = f"{vna_amplitude_name}/{fname}"
            self.measure_IV(
                name, 
                amplitude=amplitude, 
                period=period, 
                offset_time=offset_time, 
                sweep_time=sweep_time
                )
                
        self.save_state()

    def position_study(
            self,
            pos_inc,
            pos_end,
            motor_speed = None,
            save_amp = None,
            voltage = None,
            period = None,
            sweep_time = None,
            offset_time = None,
            position_name = None,
            ramp_cool_down = None,
            meas_cool_down = None,
    ):

    # motor_speed = 20, pos_inc=1e-5  equals 1s movement

        if save_amp is None:
            save_amp = self.save_amp
        if voltage is None:
            voltage = self.voltage
        if motor_speed is None:
            motor_speed = self.motor_speed
        if ramp_cool_down is None:
            ramp_cool_down = self.ramp_cool_down
        if meas_cool_down is None:
            meas_cool_down = self.meas_cool_down
        if position_name is None:
            position_name = self.position_name
            
        # setup general stuff
        self.gw.adwin.setAveraging(self.adwin_average)
        self.gw.magnet.set_rate(self.magnet_rate)
        self.gw.magnet.goto_zero()
        self.gw.motor.set_target_speed(20)

        # get position
        pos_start = self.gw.motor.get_status()['position']
        positions = np.linspace(pos_start, pos_end, int((pos_end-pos_start)/pos_inc))

        amp_i = 0
        ampBs = [10, 100, 1000, 10000]
        for i, pos in enumerate(tqdm(positions)):
            fname = f'pos={pos:+.8f}'

            self.femto1_amp = 1000
            self.gw.femtos.set_amplification_A(1000)
            self.femto2_amp = 10
            self.gw.femtos.set_amplification_B(10)
            
            # go to position
            self.gw.motor.set_target_position(pos)
            self.gw.motor.set_moving(True)
            while self.gw.motor.get_status()['moving']:
                sleep(.1)
            
            # get amplitude
            name = f"{position_name}/{fname}/set_voltage"
            self.measure_IV(
                name, 
                amplitude=save_amp, 
                period=1, 
                offset_time=0.1, 
                sweep_time=1.1
                )
            get_name = f'measurement/{position_name}/{fname}/set_voltage/sweep/adwin'
            v1 = self.dgw.get_data(get_name, 'V1') / self.femto1_amp
            max_v1 = np.max(np.abs(v1))
            amplitude = np.min([voltage / max_v1 * save_amp, 10])

            # get amplification
            iter = 0
            while True:    
                name = f"{position_name}/{fname}/ampB={ampBs[amp_i]}"                
                self.femto2_amp = ampBs[amp_i]
                self.gw.femtos.set_amplification_B(ampBs[amp_i])
                self.measure_IV(
                    name, 
                    amplitude=amplitude, 
                    period=1, 
                    offset_time=0.1, 
                    sweep_time=1.1
                    )
                get_name = f'measurement/{position_name}/{fname}/ampB={ampBs[amp_i]}/sweep/adwin'
                v2 = self.dgw.get_data(get_name, 'V2')
                max_v2 = np.max(np.abs(v2))
                
                if 0.95 <= max_v2 <= 9.5:
                    break 
                if max_v2 < 0.95:
                    if amp_i == 3:
                        break
                    amp_i += 1
                if max_v2 > 9.5:
                    if amp_i == 0:
                        break
                    amp_i -= 1
                if iter >= 10:
                    break
                iter += 1
            
            # do IV sweep
            name = f"{position_name}/{fname}"
            self.measure_IV(
                name, 
                amplitude=amplitude, 
                period=period, 
                offset_time=offset_time, 
                sweep_time=sweep_time
                )

        # end of study
        self.save_state()

        
    def time_study(
            self,
            amplitude = None,
            period = None,
            sweep_time = None,
            femto1_amp = None,
            femto2_amp = None,
            offset_time = None,
            time_name = None,
            ramp_cool_down = None,
            meas_cool_down = None,
                             ):
                
        if femto1_amp is None:
            femto1_amp = self.femto1_amp        
        if femto2_amp is None:
            femto2_amp = self.femto2_amp  
        if time_name is None:
            time_name = self.time_name
        if ramp_cool_down is None:
            ramp_cool_down = self.ramp_cool_down
        if meas_cool_down is None:
            meas_cool_down = self.meas_cool_down

        # setup general stuff
        self.gw.adwin.setAveraging(self.adwin_average)
        self.gw.adwin.setOutput(False)
        self.gw.adwin.setSweeping(False)
        self.gw.adwin.setAmplitude(0)
        self.gw.femtos.set_amplification_A(femto1_amp)
        self.gw.femtos.set_amplification_B(femto2_amp)
        self.gw.vna.setOutput(False)
        self.gw.magnet.set_rate(self.magnet_rate)
        self.gw.magnet.goto_zero()

        try:
            i=0
            pbar = tqdm(desc='while loop')
            while True:
                fname = f'i={i:09d}'
                name = f"{time_name}/{fname}"
                self.measure_IV(
                    name, 
                    amplitude=amplitude, 
                    period=period, 
                    offset_time=offset_time, 
                    sweep_time=sweep_time
                    )
                sleep(meas_cool_down) 
                i+=1
                pbar.update(1)
        except KeyboardInterrupt:
            pbar.close()
            self.save_state()