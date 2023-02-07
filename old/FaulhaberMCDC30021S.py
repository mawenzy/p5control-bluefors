from pyvisa import ResourceManager
from logging import getLogger
from time import sleep
from threading import Thread, Event

mylogger = getLogger()


class FaulhaberMCDC3002SWorker(Thread):
    def __init__(self, address=1, name="Faulhaber Motor Worker", delay=0.1):
        super().__init__()
        self.exit_request = Event()
        self.moving = Event()
        self.stopping = Event()
        self.paused = Event()

        self.delay = delay
        self.name = name

        rm = ResourceManager()
        self.inst = rm.open_resource(f"ASRL{address}::INSTR")
        self.inst.read_termination = "\r\n"
        self.inst.timeout = 1000

        ok = self.inst.query("EN")

        if ok == "OK":
            mylogger.info(f"({self.name}) Connection is established!")
        else:
            mylogger.error(f"({self.name}) Connection was not established.")

        self.not_moving = True
        self.pos = -9999999999

    def run(self):
        while not self.exit_request.is_set():
            sleep(self.delay)
            if not self.paused.is_set():

                # Check Position
                self.get_position()

                # Start Movement
                if self.moving.is_set() and self.not_moving:
                    self.notify_position()
                    self.start_motor()

                # Stop Movement
                if self.stopping.is_set():
                    self.stop_motor()
            else:
                mylogger.debug(f"({self.name}) ... is paused!")

    def notify_query(self, string):
        reading = self.inst.query(string)
        if reading == "p":
            self.notify()
            sleep(self.delay)
            try:
                reading = self.inst.read()
            except:
                pass
        return reading

    def notify(self):
        self.moving.clear()
        self.not_moving = True
        mylogger.info(f"({self.name}) Position reached!")

    def notify_position(self):
        ok = self.notify_query("NP")
        if ok == "OK":
            mylogger.info(f"({self.name}) Notify Position started!")
        else:
            mylogger.warning(f"({self.name}) Notify Position was not started.")

    def get_position(self):
        self.pos = int(self.notify_query("POS"))
        mylogger.debug(f"({self.name}) Current position is {self.pos}.")

    def start_motor(self):
        ok = self.notify_query("M")
        if ok == "OK":
            self.moving.clear()
            self.not_moving = False
            mylogger.debug(f"({self.name}) Motor started!")
        else:
            mylogger.warning(f"({self.name}) Motor was not started.")

    def stop_motor(self):
        ok = self.notify_query("V0")
        if ok == "OK":
            self.stopping.clear()
            self.not_moving = True
            mylogger.debug(f"({self.name}) Motor stopped!")
        else:
            mylogger.warning(f"({self.name}) Motor was not stopped.")


class FaulhaberMCDC3002S:
    def __init__(self, name="Faulhaber Motor", address=1, delay=0.1):
        self.name = name
        self.address = address
        self.delay = delay
        self.target_pos = 9999999999
        self.old_target_pos = 9999999999

        # Start Thread
        self.motorThread = FaulhaberMCDC3002SWorker(
            address=self.address, delay=self.delay, name=f"{self.name} Worker"
        )
        self.motorThread.exit_request.clear()
        self.motorThread.moving.clear()
        self.motorThread.stopping.clear()
        self.motorThread.paused.clear()

        self.motorThread.start()

        # Configure Motor Settings
        self.activate_position_limits(True)
        self.lower_position_limit = -100
        self.upper_position_limit = 1.3e9

        self.maximum_speed = 6000


    def exit(self):
        self.motorThread.stopping.set()
        self.motorThread.exit_request.set()
        self.disable_motor()
        self.motorThread.inst.close()

    def disable_motor(self):
        ok = self.my_query("DI")
        if ok == "OK":
            mylogger.info(f"({self.name}) Connection is closed!")
        else:
            mylogger.error(f"({self.name}) Connection was not closed.")

    def my_query(self, string):
        self.motorThread.paused.set()
        sleep(self.motorThread.delay * 1.5)
        ok = self.motorThread.notify_query(string)
        sleep(self.motorThread.delay * 1.5)
        self.motorThread.paused.clear()
        return ok

    def activate_position_limits(self, activate=True):
        ok = self.my_query(f"APL{int(activate)}")
        string = "deactivated"
        if activate:
            string = "activated"
        if ok == "OK":
            mylogger.info(f"({self.name}) Position Limits are {string}.")
        else:
            mylogger.error(f"({self.name}) Position Limits were not {string}!")

    def start(self):
        self.motorThread.moving.set()
        sleep(self.motorThread.delay * 2)
        mylogger.info(f"({self.name}) Motor started!")

    def stop(self):
        self.motorThread.stopping.set()
        mylogger.info(f"({self.name}) Motor stopped!")

    @property
    def running(self):
        sleep(self.motorThread.delay * 2)
        return not self.motorThread.not_moving

    @property
    def position(self):
        return self.motorThread.pos

    @property
    def target_position(self):
        if not self.old_target_pos == self.target_pos:
            mylogger.info(f"({self.name}) Target Position: {self.target_pos}")
            self.old_target_pos = self.target_pos
        return self.target_pos

    @target_position.setter
    def target_position(self, target_pos):
        if self.lower_position_limit <= target_pos <= self.upper_position_limit:
            ok = self.my_query(f"LA{target_pos}")
            self.target_pos = target_pos
            if ok == "OK":
                mylogger.info(f"({self.name}) Target Position is defined as {target_pos}.")
            else:
                mylogger.error(f"({self.name}) Target Position was not defined.")
        else:
            mylogger.error(f"({self.name}) Target Position has to be within limits.")

    # TODO AC/GAC & DEC/GDEC

    @property
    def lower_position_limit(self):
        lower_limit = int(self.my_query(f"GNL"))
        mylogger.info(f"({self.name}) Lower Position Limit: {lower_limit}")
        return lower_limit

    @lower_position_limit.setter
    def lower_position_limit(self, lower_limit):
        if lower_limit < 0:
            ok = self.my_query(f"LL{lower_limit}")
            if ok == "OK":
                mylogger.info(f"({self.name}) Lower Position Limit is defined.")
            else:
                mylogger.error(f"({self.name}) Lower Position Limit was not defined.")
        else:
            mylogger.error(f"({self.name}) Lower Position Limit has to be negative.")

    @property
    def upper_position_limit(self):
        upper_limit = int(self.my_query(f"GPL"))
        mylogger.info(f"({self.name}) Upper Position Limit: {upper_limit}")
        return upper_limit

    @upper_position_limit.setter
    def upper_position_limit(self, upper_limit):
        if upper_limit >= 0:
            ok = self.my_query(f"LL{upper_limit}")
            if ok == "OK":
                mylogger.info(f"({self.name}) Upper Position Limit is defined.")
            else:
                mylogger.error(f"({self.name}) Upper Position Limit was not defined.")
        else:
            mylogger.error(f"({self.name}) Upper Position Limit has to be positive.")

    @property
    def maximum_speed(self):
        maximum_speed = int(self.my_query(f"GSP"))
        mylogger.info(f"({self.name}) Maximum Speed: {maximum_speed}")
        return maximum_speed

    @maximum_speed.setter
    def maximum_speed(self, maximum_speed):
        if maximum_speed >= 0:
            ok = self.my_query(f"SP{maximum_speed}")
            if ok == "OK":
                mylogger.info(f"({self.name}) Maximum Speed is defined.")
            else:
                mylogger.error(f"({self.name}) Maximum Speed was not defined.")
        else:
            mylogger.error(f"({self.name}) Maximum Speed has to be positive.")



'''
class MOTOR(ThreadingInstrument):
    """ Motor address"""
    installed_motor = "ASRL3"
    max_I = 220
    max_rpm = 8000
    encoder = 1024
    reduction = 3088

    """ Motor address"""
    installed_motor = "COM1"
    max_I = 300
    max_rpm = 8000
    encoder = 1024
    reduction = 3088

    """ Motor address"""
    installed_motor = u'ASRL22'#u'ASRL24::INSTR' #u'ASRL22::INSTR' Achtung wo der Motor
    #eingesteckt ist -> keine kopplung zwischen den Phasen herstellen!!
    max_I = 220
    max_rpm = 7800
    encoder = 1024
    reduction = 1734

    def initialize_device(self):
        """Sets some variables"""
        self.encoder = config.encoder
        self.reduction = config.reduction
        self.max_rpm = config.max_rpm
        self.max_I = config.max_I
        self.higher_bound = False
        self.lower_bound = False

        self._gearfact = self.reduction * self.encoder * 4

        self.write('V0')  # speed = 0 rpm
        self.write('AC500')  # acceleration
        self.write('DEC500')
        self.set_current(self.max_I)  # max current in mA
        self.write('SP%i' % (self.max_rpm))  # maximum rpm
        self.write('EN')  # enable movement

        self.limit_low = -25
        self.limit_high = 0
        self._mpos = 0
        self._v = 0
        self._current = 0
        self._gv = self.update_set_velocity()

        self.data["timestamp"] = []
        self.data["position"] = []
        self.data["current"] = []
        self.data["velocity"] = []

        log("Motor initialized")

        self.disable()
        log("Motor has been disabled for noise reduction")

    def get_errors(self):
        """Prints the devices errors"""
        return "000"

    def disable(self):
        """stop motor and deactivate motor control"""
        self.write('V0')
        self._mpos = float(self.get_pos())
        self.write('DI')

    def enable(self):
        """enables motor"""
        self.write('EN')

    def stop(self):
        """stop the motor (3x)"""
        for i in range(3):
            self.set_velocity(0)
        self.disable()

    def get_pos(self):
        """return actual motor position of its encoder
            in encoder steps"""
        return self._mpos

    def get_real_pos(self, counts=None):
        """converts actual position to turns of the screw"""
        if counts == None:
            position = self.get_pos()
        else:
            position = float(counts)
        return float(position / self._gearfact)

    def get_velocity(self):
        """return the current velocity"""
        return self._v

    def update_set_velocity(self):
        answer = self.ask('GV')  # update speed
        try:
            speed = float(answer.strip())
        except:
            speed = 0
            log("Bad Answer!")
            print
            answer
        return speed

    def set_velocity(self, speed):
        """sets the velocity"""

        self.write('V' + str(speed))
        self._gv = speed

    def set_home(self, addr=None):
        """sets HOME"""
        if addr == None:
            self.write('HO')
        else:
            self.write('HO' + str(addr))

    def get_temperature(self):
        """gets temperature"""
        return float(self.ask("TEM"))

    def set_current(self, limit=50):
        """sets the current limit in mA"""
        self.write('LCC%i' % (int(limit)))

    def get_current(self):
        """returns current"""
        return self._current

    def goto_pos(self, destination=0, speed=5000):
        """drives the motor to a defined position in rounds, the function
        converts it into counts."""
        # self.motor.ask('SP'+str(speed)) # max speed
        self.enable()
        newpos = long(destination * self._gearfact)
        self.write('SP' + str(speed))  # set maximum speed
        self.write('LA' + str(newpos))  # set position
        self.write('M')  # move

    def set_lower_limit(self, limit=-25):
        self.limit_low = limit

    def set_upper_limit(self, limit=0):
        self.limit_high = limit

    def get_data(self):
        """Main function for thread to gather data"""
        answer = ""
        try:
            answer = self.ask('GN')  # update speed
            self._v = float(answer.strip())
        except:
            self._v = -1
            log("Bad Answer Velocity")
            log(answer)

        try:
            answer = self.ask('POS')  # update position
            self._mpos = float(answer.strip())
        except:
            self._mpos = -1
            log("Bad Answer Position")
            log(answer)

        try:
            answer = self.ask("GRC")  # update current
            self._current = float(answer.strip())
        except:
            self._current = -1
            log("Bad Answer Current")
            log(answer)

        # self._current = -1

        # check if the motor is running
        running = True
        if self._v == 0:
            running = False

        # set flags for lower and higher bound
        if abs(self.get_real_pos() - self.limit_high) < 0.1:
            self.higher_bound = True
            log("Upper bound hit!")
        else:
            self.higher_bound = False
        if abs(self.get_real_pos() - self.limit_low) < 0.1:
            self.lower_bound = True
            log("Lower bound hit!")
        else:
            self.lower_bound = False

        return {"timestamp": [time.time()], "position": [self.get_real_pos()],
                "current": [self.get_current()], "velocity": [self.get_velocity()]}

    def thread_error(self):
        """Is called when an error occured while aquiring data from device"""
        self.device.clear()
'''
