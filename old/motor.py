

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
