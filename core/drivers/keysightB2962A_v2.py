"""
Driver for KEYSIGHT B2962A Power Source
"""
import logging

from p5control.drivers.basedriver import BaseDriver, ThreadSafeBaseDriver
from p5control import DataGateway, InstrumentGateway

logger = logging.getLogger(__name__)

class KeysightB2962A_v2(ThreadSafeBaseDriver):
    """
    Driver for KEYSIGHT B2962A Power Source
    """

    def open(self):
        logger.debug('%s.open()', self._name)
        super().open()

        # setup termination
        self._inst.write_termination = "\n"
        self._inst.read_termination = "\n"

        # copied from olli driver
        self.timeout(10000)
        self.initialize()

    def close(self):
        self.reset()
        self._inst.close()
        logger.debug('%s.close()', self._name)
    """
    Status measurement
    """
    def get_status(self):
        logger.debug('%s.get_status()', self._name)
        return {
            "output": self.output,
            "sweeping": self.sweeping,
            "amplitude": self.amplitude,
            "period": self.period,
            # "max_current": self.max_current,
        }
        
    def timeout(self, timeout):
        logger.debug('%s.timeout()', self._name)
        self._inst.timeout = int(timeout)

    def initialize(self):
        logger.debug('%s.initialize()', self._name)
        self.reset()
        self.triangle_mode()

        self.output = False
        self.sweeping = False

        self.set_amplitude(0)
        self.set_period(1)
        # self.set_max_current(1)

    def reset(self):
        logger.debug('%s.reset()', self._name)
        with self.lock:
            self._inst.write("*CLS") # clear status command
            self._inst.write("*RST") # reset the instrument for SCPI operation
            self._inst.query("*OPC?") # wait for the operation to complete

    def triangle_mode(self): 
        logger.debug('%s.triangle_mode()', self._name)       
        with self.lock:
            self._inst.write(f":sour1:func:mode volt")
            self._inst.write(f":sour2:func:mode volt")
            self._inst.write(f":sour1:volt:mode arb")
            self._inst.write(f":sour2:volt:mode arb")
            self._inst.write(f":sour1:arb:func tri")
            self._inst.write(f":sour2:arb:func tri")
            self._inst.write(f":sour1:arb:count inf")
            self._inst.write(f":sour2:arb:count inf")
            self._inst.write(f":sour1:arb:volt:tri:star:time 0")
            self._inst.write(f":sour2:arb:volt:tri:star:time 0")
            self._inst.write(f":sour1:arb:volt:tri:end:time 0")
            self._inst.write(f":sour2:arb:volt:tri:end:time 0")
            self._inst.write(f":trig1:tran:sour aint")
            self._inst.write(f":trig2:tran:sour aint")
            self._inst.write(f":trig1:tran:coun 10000")
            self._inst.write(f":trig2:tran:coun 10000")
            
            self._inst.write(f':SENSe1:FUNCtion:ON "CURR"')
            self._inst.write(f':SENSe2:FUNCtion:ON "CURR"')
            self._inst.write(f":SENSe1:CURR:DC:PROTection:LEVel:BOTH 1") # Keysight B2962A SCPI, p76, 2-36, table 2-5
            self._inst.write(f":SENSe2:CURR:DC:PROTection:LEVel:BOTH 1") # cry, like you should. Because this is bullshit!
    
    # def set_max_current(self, max_current):
    #     logger.debug('%s.set_max_current()', self._name)
    #     with self.lock:
    #         self._inst.write(f":OUTPut:PROTection:STATe OFF")
    #         self._inst.write(f":SENSe2:CURRent:DC:PROTection:LEVel:BOTH {max_current}")
    #     self.max_current = max_current

    # def get_max_current(self):
    #     logger.debug('%s.get_max_current()', self._name)
    #     return self.max_current

    def set_output(self, output):
        logger.debug('%s.set_output()', self._name)
        if output:  
            with self.lock:
                self._inst.write("outp1 on")
                self._inst.write("outp2 on")
        else:
            if self.sweeping:
                self.reset()
                self.triangle_mode()
                self.reset_amplitude()
                self.reset_period()
                self.sweeping = False
            else:
                with self.lock:
                    self._inst.write("outp1 off")
                    self._inst.write("outp2 off")
        self.output = output

    def get_output(self):
        logger.debug('%s.get_output()', self._name)
        return self.output
    
    def set_sweeping(self, sweeping):
        logger.debug('%s.set_sweeping()', self._name)
        if self.output:
            if sweeping and not self.sweeping:
                with self.lock:
                    self._inst.write("INIT (@1,2)")
            if not sweeping and self.sweeping:
                self.reset()
                self.triangle_mode()
                self.reset_amplitude()
                self.reset_period()
                self.output = False
            self.sweeping = sweeping

    def get_sweeping(self):
        logger.debug('%s.get_sweeping()', self._name)
        return self.sweeping        

    def set_amplitude(self, amplitude): 
        logger.debug('%s.set_amplitude()', self._name)     
        with self.lock:
            self._inst.write(f":sour1:volt {amplitude}")
            self._inst.write(f":sour2:volt {-amplitude}")
            self._inst.write(f":sour1:arb:volt:tri:star {amplitude}")
            self._inst.write(f":sour2:arb:volt:tri:star {-amplitude}")
            self._inst.write(f":sour1:arb:volt:tri:top {-amplitude}")
            self._inst.write(f":sour2:arb:volt:tri:top {amplitude}")
        self.amplitude = amplitude

    def get_amplitude(self):
        logger.debug('%s.get_amplitude()', self._name)
        return self.amplitude
    
    def reset_amplitude(self):
        logger.debug('%s.reset_amplitude()', self._name)
        with self.lock:
            self._inst.write(f":sour1:volt {self.amplitude}")
            self._inst.write(f":sour2:volt {-self.amplitude}")
            self._inst.write(f":sour1:arb:volt:tri:star {self.amplitude}")
            self._inst.write(f":sour2:arb:volt:tri:star {-self.amplitude}")
            self._inst.write(f":sour1:arb:volt:tri:top {-self.amplitude}")
            self._inst.write(f":sour2:arb:volt:tri:top {self.amplitude}")

    
    def set_period(self, period):  
        logger.debug('%s.set_period()', self._name)  
        with self.lock:
            self._inst.write(f":sour1:arb:volt:tri:rtim {period/2}")
            self._inst.write(f":sour2:arb:volt:tri:rtim {period/2}")
            self._inst.write(f":sour1:arb:volt:tri:ftim {period/2}")
            self._inst.write(f":sour2:arb:volt:tri:ftim {period/2}")
        self.period = period
        
    def get_period(self):
        logger.debug('%s.get_period()', self._name)
        return self.period
    
    def reset_period(self):
        logger.debug('%s.reset_period()', self._name)
        with self.lock:
            self._inst.write(f":sour1:arb:volt:tri:rtim {self.period/2}")
            self._inst.write(f":sour2:arb:volt:tri:rtim {self.period/2}")
            self._inst.write(f":sour1:arb:volt:tri:ftim {self.period/2}")
            self._inst.write(f":sour2:arb:volt:tri:ftim {self.period/2}")
            

