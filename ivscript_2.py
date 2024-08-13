from p5control import InstrumentServer, InstrumentGateway, DataGateway
from p5control.server.inserv import InstrumentServerError

from time import sleep, time
import numpy as np
from tqdm import tqdm
from tqdm.contrib.itertools import product

from core.drivers_v2.adwingold2_v6 import ADwinGold2
from core.drivers_v2.femto_v2 import Femto
from core.drivers_v2.rref import Rref
from core.drivers_v2.blueforsapi_v2 import BlueForsAPI
from core.drivers_v2.ami430_v2 import AMI430
from core.drivers_v2.vna_v2 import ZNB40_source
from core.drivers_v2.yoko_v2 import YokogawaGS200
from core import Faulhaber

import logging
logger = logging.getLogger(__name__)

class BlueforsServer_v2():
    def __init__(self):
        pass

    def start_server(
            self, 
            server_name = None,
            S = '11',
            R_ref= 5.2e4,
            ):
        
        
        if server_name is None:
            self.inserv = InstrumentServer()
            logging.basicConfig(
                filename=f'.data/iv_script_v2_{time()}.log',
                level=logging.DEBUG,
                filemode='w', # overwrites logs every time this script is started
                format='%(asctime)s.%(msecs)03d %(levelname)-8s %(thread)6d %(name)-30s %(funcName)-20s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
            )
        else:
            self.inserv = InstrumentServer(data_server_filename=server_name)
            logging.basicConfig(
                filename=f'{server_name[:-5]}.log',
                level=logging.DEBUG,
                filemode='w', # overwrites logs every time this script is started
                format='%(asctime)s.%(msecs)03d %(levelname)-8s %(thread)6d %(name)-30s %(funcName)-20s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
            )

        """
        Add Devices
        """
        self.inserv._add('adwin', ADwinGold2, series_resistance=0)
        self.inserv._add('rref',  Rref, R_ref = R_ref) # 100kOhm
        self.inserv._add('femto', Femto)
        self.inserv._add('vna',   ZNB40_source, S = S)
        self.inserv._add('gate',  YokogawaGS200)
        self.inserv._add('bluefors', BlueForsAPI) # try to remove errors of sampleheater
        self.inserv._add('magnet', AMI430) # untested
        self.inserv._add('motor',  Faulhaber)
        self.inserv.start()  

    def stop_server(self):        
        self.inserv.stop()
        self.inserv._remove('femto')
        self.inserv._remove('vna')
        self.inserv._remove('gate')
        self.inserv._remove('magnet')


class MeasurementScript_v2():
    
    def __init__(self):        
        self.gw = InstrumentGateway()
        self.gw.connect()

        self.dgw = DataGateway()
        self.dgw.connect()
        
        self.offset_name = 'offset'
        self.sweep_name = 'sweep'
        self.iv_name = 'single_IV'
        self.gate_voltages_name = 'gate_voltages'
        self.magnetic_fields_name = 'magnetic_fields'
        self.vna_irradiations_name = 'vna_irradiations'
        self.vna_frequencies_name = 'vna_frequencies'
        self.vna_amplitudes_name = 'vna_amplitudes'
        self.temperatures_name = 'temperatures'

        #self.time_name = 'time_evolution'
        #self.position_name = 'motor_positions'
    
        self.adwin_sample_rate = 4000
        self.femto1_amp = 1
        self.femto2_amp = 1
        self.magnet_rate = 0

        self.initial_ramp_cool_down = 600
        self.ramp_cool_down = 10
        self.heater_cool_down = 10
        self.offset_cool_down = 0
        self.sweep_cool_down = 0
        self.meas_delay_time = .5

        self.amplitude = 0
        self.period = 28.0327 # equals 35.673mHz, 50Hz equals 20 ms
        self.sweep_time = 30
        self.offset_time = 3
        
        self.voltage = 0.002 # V
        self.save_amp = .5
        self.motor_speed = 20

        self.initialize_devices()
    
    def initialize_devices(self):    
        self.gw.magnet.set_rate(self.magnet_rate)  
        self.gw.vna.setOutput(False) 
        self.gw.gate.setOutput(False)

        self.gw.adwin.setSampleRate(self.adwin_sample_rate)
        self.gw.adwin.setSweeping(False)
        self.gw.adwin.setOutput(False)
        self.gw.adwin.setCalculating(False)

    def save_state(self):
        self.gw.magnet.set_rate(0)  
        self.gw.magnet.set_target_field(0) 
        self.gw.magnet.ramp() 
        self.gw.magnet.ramp() 

        self.gw.vna.setOutput(False)
        self.gw.gate.setOutput(False)
        self.gw.bluefors.setManualMode(False)
        self.gw.bluefors.setPIDMode(False)

        self.gw.adwin.setAmplitude(0)
        self.gw.adwin.setSweeping(False)
        self.gw.adwin.setOutput(False)

    def name_generator(
        self,
        gate_voltage=None,
        vna_frequency=None,
        vna_amplitude=None,
        magnetic_field=None,
        motor_position=None,
        heater_power=None,
        ):
        
        string = ''
        if gate_voltage is not None:
            string += f' gate_{gate_voltage*1e3:+07.4f}mV'
        if vna_frequency is not None or vna_amplitude is not None:
            string += ' vna'
            if vna_frequency is not None:
                string += f'_{vna_frequency*1e-9:02.4f}GHz'
            if vna_amplitude is not None:
                string += f'_{vna_amplitude:.3f}V'
        if magnetic_field is not None:
            string += f' magnet_{magnetic_field*1e3:+.2f}mT'
        if motor_position is not None:
            string += f' motor_{motor_position:+2.8f}'
        if heater_power is not None:
            string += f' heater_{heater_power*1e6:09.3f}µW'
        return string

    def setup_magnet(self, magnetic_field, ramp_cool_down):
        self.gw.magnet.set_rate(self.magnet_rate)
        if ramp_cool_down is None:
            ramp_cool_down = self.ramp_cool_down
        if magnetic_field is not None:
            self.gw.magnet.set_target_field(magnetic_field) # magnet takes T
            self.gw.magnet.ramp()
            self.gw.magnet.ramp()
            sleep(ramp_cool_down)      
        else:
            self.gw.magnet.set_target_field(0) 
            self.gw.magnet.ramp() 
            self.gw.magnet.ramp()
            magnetic_field = 0
        return magnetic_field
    
    def setup_heater(self, manual_value, heater_cool_down):
        self.gw.bluefors.setRange(6)
        if manual_value is not None:
            self.gw.bluefors.setManualValue(manual_value)
            self.gw.bluefors.setManualMode(True)
        else:
            manual_value = np.nan
        if heater_cool_down is None:
            heater_cool_down = self.heater_cool_down
        sleep(heater_cool_down)
        return manual_value
    
    def setup_gate(self, gate_voltage):
        if gate_voltage is not None:
            self.gw.gate.setVoltage(gate_voltage)
            self.gw.gate.setOutput(True)
        else:
            gate_voltage = np.nan
        return gate_voltage
    
    def setup_vna(self, vna_frequency, vna_amplitude):
        if vna_amplitude is not None and vna_frequency is not None:
            self.gw.vna.setAmplitude(vna_amplitude)
            self.gw.vna.setFrequency(vna_frequency) # vna takes Hz
            self.gw.vna.setOutput(True)
        else:
            vna_frequency, vna_amplitude = np.nan, np.nan 
        return vna_frequency, vna_amplitude
    
    def setup_femtos(self, femto1_amp, femto2_amp):
        if femto1_amp is None:
            femto1_amp = self.femto1_amp        
        if femto2_amp is None:
            femto2_amp = self.femto2_amp  
        self.gw.femto.set_amp(femto1_amp, 'A')
        self.gw.femto.set_amp(femto2_amp, 'B')

    def setup_adwin(self, sample_rate): 
        if sample_rate is None:
            sample_rate = self.adwin_sample_rate  
        self.gw.adwin.setSampleRate(sample_rate)

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
        sleep(self.offset_cool_down)

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
        sleep(self.sweep_cool_down)

    """
        Here the actual scripts are starting.
    """

    def single_IV(
            self,
            iv_name = None,
            amplitude = None,
            period = None,
            sweep_time = None,
            offset_time = None,
            sample_rate = None,
            femto1_amp = None,
            femto2_amp = None,
            magnetic_field = None,
            gate_voltage = None,
            vna_amplitude = None,
            vna_frequency = None,            
                    ):
        
        # Genereate Name
        if iv_name is None:
            iv_name = self.iv_name
        iv_name += self.name_generator(
            gate_voltage=gate_voltage, 
            vna_amplitude=vna_amplitude, 
            vna_frequency=vna_frequency, 
            magnetic_field=magnetic_field,
            )
        
        # setup general stuff
        self.setup_adwin(sample_rate)
        self.setup_femtos(femto1_amp, femto2_amp)

        # setup magnet, gate, vna
        magnetic_field = self.setup_magnet(magnetic_field, self.initial_ramp_cool_down)
        gate_voltage = self.setup_gate(gate_voltage)
        vna_frequency, vna_amplitude = self.setup_vna(vna_frequency, vna_amplitude)

        # do IV sweep
        self.measure_IV(
            iv_name, 
            amplitude=amplitude, 
            period=period, 
            offset_time=offset_time, 
            sweep_time=sweep_time
            )
        
    def gate_study(
            self,
            gate_voltages,
            gate_voltages_name = None,
            amplitude = None,
            period = None,
            sweep_time = None,
            offset_time = None,
            sample_rate = None,
            femto1_amp = None,
            femto2_amp = None,
            magnetic_field = None,
            vna_amplitude = None,
            vna_frequency = None,  
                        ):

        # Genereate Name
        if gate_voltages_name is None:
            gate_voltages_name = self.gate_voltages_name 
        gate_voltages_name += self.name_generator(
            vna_amplitude=vna_amplitude, 
            vna_frequency=vna_frequency, 
            magnetic_field=magnetic_field,
            )  
        
        # setup general stuff
        self.setup_adwin(sample_rate)
        self.setup_femtos(femto1_amp, femto2_amp)

        # setup magnet, gate, vna
        magnetic_field = self.setup_magnet(magnetic_field, self.initial_ramp_cool_down)
        vna_frequency, vna_amplitude = self.setup_vna(vna_frequency, vna_amplitude)

        # do IV sweep
        name = f"{gate_voltages_name}/no_gate"
        self.measure_IV(
            name, 
            amplitude=amplitude, 
            period=period, 
            offset_time=offset_time, 
            sweep_time=sweep_time
            )
        
        for _, gate_voltage in enumerate(tqdm(gate_voltages)):
            fname = self.name_generator(gate_voltage=gate_voltage)[1:]
            
            # ramp to field
            _ = self.setup_gate(float(gate_voltage))

            # do IV sweep
            self.measure_IV(
                f"{gate_voltages_name}/{fname}", 
                amplitude=amplitude, 
                period=period, 
                offset_time=offset_time, 
                sweep_time=sweep_time
                )
            self.gw.gate.setOutput(False)

        self.save_state()

    def magnetic_field_study(
            self,
            magnetic_fields,
            magnetic_fields_name = None,
            amplitude = None,
            period = None,
            sweep_time = None,
            offset_time = None,
            sample_rate = None,
            femto1_amp = None,
            femto2_amp = None,
            gate_voltage = None,
            vna_amplitude = None,
            vna_frequency = None,  
                        ):
        
        # Genereate Name
        if magnetic_fields_name is None:
            magnetic_fields_name = self.magnetic_fields_name
        magnetic_fields_name += self.name_generator(
            gate_voltage=gate_voltage, 
            vna_amplitude=vna_amplitude, 
            vna_frequency=vna_frequency, 
            )
        
        # setup general stuff
        self.setup_adwin(sample_rate)
        self.setup_femtos(femto1_amp, femto2_amp)

        # setup magnet, gate, vna
        gate_voltage = self.setup_gate(gate_voltage)
        vna_frequency, vna_amplitude = self.setup_vna(vna_frequency, vna_amplitude)

        # do IV sweep
        name = f"{magnetic_fields_name}/no_field"
        self.measure_IV(
            name, 
            amplitude=amplitude, 
            period=period, 
            offset_time=offset_time, 
            sweep_time=sweep_time
            )
        
        # Ramp to initial field and wait initial_ramp_cool_down s
        magnetic_field = self.setup_magnet(magnetic_fields[0], self.initial_ramp_cool_down)
        
        for _, magnetic_field in enumerate(tqdm(magnetic_fields)):
            fname = self.name_generator(magnetic_field=magnetic_field)[1:]
            
            # ramp to field
            _ = self.setup_magnet(magnetic_field, self.ramp_cool_down)

            # do IV sweep
            self.measure_IV(
                f"{magnetic_fields_name}/{fname}", 
                amplitude=amplitude, 
                period=period, 
                offset_time=offset_time, 
                sweep_time=sweep_time
                )

        self.save_state()
        sleep(self.initial_ramp_cool_down)

    def irradiation_study(
            self,
            vna_frequencies,
            vna_amplitudes,
            vna_irradiations_name = None,
            amplitude = None,
            period = None,
            sweep_time = None,
            offset_time = None,
            sample_rate = None,
            femto1_amp = None,
            femto2_amp = None,
            gate_voltage = None,
            magnetic_field = None, 
                             ):

        # Generate Name
        if vna_irradiations_name is None:
            vna_irradiations_name = self.vna_irradiations_name
        vna_irradiations_name += self.name_generator(
            gate_voltage=gate_voltage, 
            magnetic_field=magnetic_field,
            )      
                
        # setup general stuff
        self.setup_adwin(sample_rate)
        self.setup_femtos(femto1_amp, femto2_amp)

        # setup magnet, gate, vna
        magnetic_field = self.setup_magnet(magnetic_field, self.initial_ramp_cool_down)
        gate_voltage = self.setup_gate(gate_voltage)

        # do IV sweep
        name = f"{vna_irradiations_name}/no_irradiation"
        self.measure_IV(
            name, 
            amplitude=amplitude, 
            period=period, 
            offset_time=offset_time, 
            sweep_time=sweep_time
            )
        
        for vna_frequency, vna_amplitude in product(vna_frequencies, vna_amplitudes):
            vna_frequency, vna_amplitude = float(vna_frequency), float(vna_amplitude)
            
            fname = self.name_generator(
                vna_frequency=vna_frequency,
                vna_amplitude=vna_amplitude,
                )[1:]
            
            # setup vna
            self.setup_vna(vna_frequency, vna_amplitude)

            # do IV sweep
            self.measure_IV(
                f"{vna_irradiations_name}/{fname}", 
                amplitude=amplitude, 
                period=period, 
                offset_time=offset_time, 
                sweep_time=sweep_time
                )
            self.gw.vna.setOutput(False)

        self.save_state()

    def frequency_study(
            self,
            vna_frequencies,
            vna_amplitude,
            vna_frequencies_name = None,
            amplitude = None,
            period = None,
            sweep_time = None,
            offset_time = None,
            sample_rate = None,
            femto1_amp = None,
            femto2_amp = None,
            gate_voltage = None,
            magnetic_field = None, 
                             ):
        
        if vna_frequencies_name is None:
            vna_frequencies_name = self.vna_frequencies_name
        vna_frequencies_name += self.name_generator(vna_amplitude=vna_amplitude)[4:]
        
        self.irradiation_study(
            vna_frequencies=vna_frequencies,
            vna_amplitudes=np.array([vna_amplitude]),
            vna_irradiations_name = vna_frequencies_name,
            amplitude = amplitude,
            period = period,
            sweep_time = sweep_time,
            offset_time = offset_time,
            sample_rate = sample_rate,
            femto1_amp = femto1_amp,
            femto2_amp = femto2_amp,
            gate_voltage = gate_voltage,
            magnetic_field = magnetic_field, 
                             )

    def amplitude_study(
            self,
            vna_amplitudes,
            vna_frequency,
            vna_amplitudes_name = None,
            amplitude = None,
            period = None,
            sweep_time = None,
            offset_time = None,
            sample_rate = None,
            femto1_amp = None,
            femto2_amp = None,
            gate_voltage = None,
            magnetic_field = None, 
                             ):
        
        if vna_amplitudes_name is None:
            vna_amplitudes_name = self.vna_amplitudes_name
        vna_amplitudes_name += self.name_generator(vna_frequency=vna_frequency)[4:]
        
        self.irradiation_study(
            vna_amplitudes=vna_amplitudes,
            vna_frequencies=np.array([vna_frequency]),
            vna_irradiations_name = vna_amplitudes_name,
            amplitude = amplitude,
            period = period,
            sweep_time = sweep_time,
            offset_time = offset_time,
            sample_rate = sample_rate,
            femto1_amp = femto1_amp,
            femto2_amp = femto2_amp,
            gate_voltage = gate_voltage,
            magnetic_field = magnetic_field, 
                             )
    
    def temperature_study(
            self,
            temperatures,
            temperatures_name = None,
            relaxation_turns = None,
            amplitude = None,
            period = None,
            sweep_time = None,
            offset_time = None,
            sample_rate = None,
            femto1_amp = None,
            femto2_amp = None,
            gate_voltage = None,
            magnetic_field = None,
            vna_amplitude = None,
            vna_frequency = None,  
                        ):
        
        # Genereate Name
        if temperatures_name is None:
            temperatures_name = self.temperatures_name
        temperatures_name += self.name_generator(
            gate_voltage=gate_voltage, 
            magnetic_field=magnetic_field,
            vna_amplitude=vna_amplitude, 
            vna_frequency=vna_frequency, 
            )
        
        # setup general stuff
        self.setup_adwin(sample_rate)
        self.setup_femtos(femto1_amp, femto2_amp)

        # setup magnet, gate, vna
        magnetic_field = self.setup_magnet(magnetic_field, self.initial_ramp_cool_down)
        gate_voltage = self.setup_gate(gate_voltage)
        vna_frequency, vna_amplitude = self.setup_vna(vna_frequency, vna_amplitude)

        # setup general stuff
        self.setup_adwin(sample_rate)
        self.setup_femtos(femto1_amp, femto2_amp)

        # setup magnet, gate, vna
        gate_voltage = self.setup_gate(gate_voltage)
        vna_frequency, vna_amplitude = self.setup_vna(vna_frequency, vna_amplitude)

        # do IV sweep
        name = f"{temperatures_name}/no_heater"
        self.measure_IV(
            name, 
            amplitude=amplitude, 
            period=period, 
            offset_time=offset_time, 
            sweep_time=sweep_time
            )
        
        # Ramp to initial temperature
        heater_powers = np.exp(2.479 * np.log(temperatures * 0.06515603))
        if relaxation_turns is not None:
            zero_turns = np.zeros(relaxation_turns)
            index = 0
            heater_powers = np.concatenate((heater_powers, zero_turns))

        _ = self.setup_heater(heater_powers[0], self.heater_cool_down)
        
        for _, heater_power in enumerate(tqdm(heater_powers)):
            fname = self.name_generator(heater_power=heater_power)[1:]
            if heater_power == 0:
                fname += f'_{index:03d}'
                index += 1
            
            # ramp to field
            _ = self.setup_heater(float(heater_power), self.heater_cool_down)

            # do IV sweep
            self.measure_IV(
                f"{temperatures_name}/{fname}", 
                amplitude=amplitude, 
                period=period, 
                offset_time=offset_time, 
                sweep_time=sweep_time
                )

        self.save_state()
        

    # def position_study(
    #         self,
    #         pos_inc,
    #         pos_end,
    #         motor_speed = None,
    #         save_amp = None,
    #         voltage = None,
    #         period = None,
    #         sweep_time = None,
    #         offset_time = None,
    #         position_name = None,
    #         ramp_cool_down = None,
    #         meas_cool_down = None,
    # ):

    # # motor_speed = 20, pos_inc=1e-5  equals 1s movement

    #     if save_amp is None:
    #         save_amp = self.save_amp
    #     if voltage is None:
    #         voltage = self.voltage
    #     if motor_speed is None:
    #         motor_speed = self.motor_speed
    #     if ramp_cool_down is None:
    #         ramp_cool_down = self.ramp_cool_down
    #     if meas_cool_down is None:
    #         meas_cool_down = self.meas_cool_down
    #     if position_name is None:
    #         position_name = self.position_name
            
    #     # setup general stuff
    #     self.gw.adwin.setAveraging(self.adwin_average)
    #     self.gw.magnet.set_rate(self.magnet_rate)
    #     self.gw.magnet.goto_zero()
    #     self.gw.motor.set_target_speed(20)

    #     # get position
    #     pos_start = self.gw.motor.get_status()['position']
    #     positions = np.linspace(pos_start, pos_end, int((pos_end-pos_start)/pos_inc))

    #     amp_i = 0
    #     ampBs = [10, 100, 1000, 10000]
    #     for i, pos in enumerate(tqdm(positions)):
    #         fname = f'pos={pos:+.8f}'

    #         self.femto1_amp = 1000
    #         self.gw.femto.set_amplification_A(1000)
    #         self.femto2_amp = 10
    #         self.gw.femto.set_amplification_B(10)
            
    #         # go to position
    #         self.gw.motor.set_target_position(pos)
    #         self.gw.motor.set_moving(True)
    #         while self.gw.motor.get_status()['moving']:
    #             sleep(.1)
            
    #         # get amplitude
    #         name = f"{position_name}/{fname}/set_voltage"
    #         self.measure_IV(
    #             name, 
    #             amplitude=save_amp, 
    #             period=1, 
    #             offset_time=0.1, 
    #             sweep_time=1.1
    #             )
    #         get_name = f'measurement/{position_name}/{fname}/set_voltage/sweep/adwin'
    #         v1 = self.dgw.get_data(get_name, 'V1') / self.femto1_amp
    #         max_v1 = np.max(np.abs(v1))
    #         amplitude = np.min([voltage / max_v1 * save_amp, 10])

    #         # get amplification
    #         iter = 0
    #         while True:    
    #             name = f"{position_name}/{fname}/ampB={ampBs[amp_i]}"                
    #             self.femto2_amp = ampBs[amp_i]
    #             self.gw.femto.set_amplification_B(ampBs[amp_i])
    #             self.measure_IV(
    #                 name, 
    #                 amplitude=amplitude, 
    #                 period=1, 
    #                 offset_time=0.1, 
    #                 sweep_time=1.1
    #                 )
    #             get_name = f'measurement/{position_name}/{fname}/ampB={ampBs[amp_i]}/sweep/adwin'
    #             v2 = self.dgw.get_data(get_name, 'V2')
    #             max_v2 = np.max(np.abs(v2))
                
    #             if 0.95 <= max_v2 <= 9.5:
    #                 break 
    #             if max_v2 < 0.95:
    #                 if amp_i == 3:
    #                     break
    #                 amp_i += 1
    #             if max_v2 > 9.5:
    #                 if amp_i == 0:
    #                     break
    #                 amp_i -= 1
    #             if iter >= 10:
    #                 break
    #             iter += 1
            
    #         # do IV sweep
    #         name = f"{position_name}/{fname}"
    #         self.measure_IV(
    #             name, 
    #             amplitude=amplitude, 
    #             period=period, 
    #             offset_time=offset_time, 
    #             sweep_time=sweep_time
    #             )

    #     # end of study
    #     self.save_state()

        
    # def time_study(
    #         self,
    #         amplitude = None,
    #         period = None,
    #         sweep_time = None,
    #         femto1_amp = None,
    #         femto2_amp = None,
    #         offset_time = None,
    #         time_name = None,
    #         ramp_cool_down = None,
    #         meas_cool_down = None,
    #                          ):
                
    #     if femto1_amp is None:
    #         femto1_amp = self.femto1_amp        
    #     if femto2_amp is None:
    #         femto2_amp = self.femto2_amp  
    #     if time_name is None:
    #         time_name = self.time_name
    #     if ramp_cool_down is None:
    #         ramp_cool_down = self.ramp_cool_down
    #     if meas_cool_down is None:
    #         meas_cool_down = self.meas_cool_down

    #     # setup general stuff
    #     self.gw.adwin.setAveraging(self.adwin_average)
    #     self.gw.adwin.setOutput(False)
    #     self.gw.adwin.setSweeping(False)
    #     self.gw.adwin.setAmplitude(0)
    #     self.gw.femto.set_amplification_A(femto1_amp)
    #     self.gw.femto.set_amplification_B(femto2_amp)
    #     self.gw.vna.setOutput(False)
    #     self.gw.magnet.set_rate(self.magnet_rate)
    #     self.gw.magnet.goto_zero()

    #     try:
    #         i=0
    #         pbar = tqdm(desc='while loop')
    #         while True:
    #             fname = f'i={i:09d}'
    #             name = f"{time_name}/{fname}"
    #             self.measure_IV(
    #                 name, 
    #                 amplitude=amplitude, 
    #                 period=period, 
    #                 offset_time=offset_time, 
    #                 sweep_time=sweep_time
    #                 )
    #             sleep(meas_cool_down) 
    #             i+=1
    #             pbar.update(1)
    #     except KeyboardInterrupt:
    #         pbar.close()
    #         self.save_state()