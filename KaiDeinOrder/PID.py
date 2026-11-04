from math import isfinite, pi, sqrt

WHEEL_DIAMETER_MM = 49.5
AXLE_TRACK_MM = 80.0
LEFT_PORT = "E"
RIGHT_PORT = "A"
LEFT_MODULE_PORT = "F"
RIGHT_MODULE_PORT = "B"

GUESS_LEFT_FORWARD_IS_CCW = True
GUESS_RIGHT_FORWARD_IS_CCW = False

LOOP_MS = 20
HEADING_KP = 4.0
HEADING_KI = 0.0

HEADING_KD = 1.0 * LOOP_MS / 1000.0
INTEGRAL_LIMIT_DEG_S = 30.0
MAX_TURN_RATE_DPS = 180.0

ACCELERATION_MM_S2 = 600.0
DECELERATION_MM_S2 = 600.0
MIN_DRIVE_SPEED_MM_S = 50.0
DISTANCE_TOLERANCE_MM = 1.0
TURN_TOLERANCE_DEG = 2.0
TURN_SETTLE_MS = 100
CURVE_TOLERANCE_DEG = 3.0
CURVE_SLOWDOWN_DEG = 10.0

MOTOR_TO_BODY_TURN = WHEEL_DIAMETER_MM / AXLE_TRACK_MM
TURN_SLOW_KP = 3.0 * MOTOR_TO_BODY_TURN
TURN_FAST_KP = 5.0 * MOTOR_TO_BODY_TURN
MIN_TURN_RATE_DPS = 30.0 * MOTOR_TO_BODY_TURN
TURN_TIMEOUT_MS = 10000
MOVE_TIMEOUT_MARGIN_MS = 3000
MOVE_TIMEOUT_FACTOR = 4.0
IMU_READY_TIMEOUT_MS = 10000

MODULE_STALL_SPEED_DPS = 300
MODULE_STALL_TIME_MS = 50

def wrap_deg(angle_deg):
    wrapped = angle_deg % 360.0
    if wrapped > 180.0:
        wrapped -= 360.0
    return wrapped

def clamp(value, limit):
    return max(-limit, min(limit, value))

def require_finite(value, name):
    if not isfinite(value):
        raise ValueError(name + " must be finite")
    return value

class HeadingPID:

    def __init__(self, kp, ki, kd, output_limit, integral_limit):
        for value in (kp, ki, kd, output_limit, integral_limit):
            require_finite(value, "PID setting")
        if output_limit <= 0 or integral_limit < 0:
            raise ValueError("invalid PID limits")
        self.kp, self.ki, self.kd = kp, ki, kd
        self.output_limit = output_limit
        self.integral_limit = integral_limit
        self.reset()

    def reset(self):
        self.integral = 0.0
        self.previous_heading = None

    def update(self, target, heading, dt):
        require_finite(target, "target")
        require_finite(heading, "heading")
        require_finite(dt, "dt")
        if dt <= 0:
            raise ValueError("dt must be positive")
        error = wrap_deg(target - heading)
        derivative = 0.0
        if self.previous_heading is not None:
            derivative = -wrap_deg(heading - self.previous_heading) / dt
        self.previous_heading = heading

        candidate = 0.0
        if self.ki:
            candidate = clamp(self.integral + error * dt, self.integral_limit)
        raw = self.kp * error + self.ki * candidate + self.kd * derivative
        output = clamp(raw, self.output_limit)

        if output == raw or error * raw <= 0:
            self.integral = candidate
        return output

class Motion:

    def __init__(self, imu, drive, wait, stopwatch):
        self.imu = imu
        self.drive = drive
        self.wait = wait
        self.stopwatch = stopwatch
        self.target_heading_deg = None
        self.heading_pid = HeadingPID(
            HEADING_KP, HEADING_KI, HEADING_KD, MAX_TURN_RATE_DPS, INTEGRAL_LIMIT_DEG_S,
        )

    def drive_heading(self, heading_deg, speed_mm_s, distance_cm, timeout_ms=None):
        try:
            self.target_heading_deg = require_finite(heading_deg, "heading")
            require_finite(speed_mm_s, "speed")
            require_finite(distance_cm, "distance")
            if distance_cm < 0:
                raise ValueError("distance must be non-negative; reverse with speed < 0")
            if distance_cm == 0:
                return
            if speed_mm_s == 0:
                raise ValueError("nonzero distance needs nonzero speed")
            direction = 1 if speed_mm_s > 0 else -1
            requested = abs(speed_mm_s)
            target_mm = distance_cm * 10.0
            baseline = require_finite(self.drive.distance(), "odometry")
            if timeout_ms is None:
                timeout_ms = MOVE_TIMEOUT_MARGIN_MS + (
                    MOVE_TIMEOUT_FACTOR * target_mm / requested * 1000.0
                )
            require_finite(timeout_ms, "timeout")
            if timeout_ms <= 0:
                raise ValueError("timeout must be positive")
            timer = self.stopwatch()
            previous_ms = -LOOP_MS
            speed = 0.0
            self.heading_pid.reset()

            while True:
                now_ms = timer.time()
                travelled = direction * (
                    require_finite(self.drive.distance(), "odometry") - baseline
                )
                remaining = target_mm - travelled
                if remaining <= DISTANCE_TOLERANCE_MM:
                    break
                if now_ms >= timeout_ms:
                    raise RuntimeError("heading move timed out; check encoders, polarity, or a blocked robot")
                dt = (now_ms - previous_ms) / 1000.0
                previous_ms = now_ms
                turn_rate = self.heading_pid.update(heading_deg, self.imu.heading(), dt)

                braking_speed = sqrt(2.0 * DECELERATION_MM_S2 * max(remaining, 0.0))
                speed = min(requested, speed + ACCELERATION_MM_S2 * dt, braking_speed)
                speed = max(min(requested, MIN_DRIVE_SPEED_MM_S), speed)

                self.drive.drive(direction * speed, turn_rate)
                self.wait(LOOP_MS)
        finally:
            self.drive.brake()

    def align(self, heading_deg, kp, timeout_ms=None):
        try:
            self.target_heading_deg = require_finite(heading_deg, "heading")
            require_finite(kp, "turn gain")
            if kp <= 0:
                raise ValueError("turn gain must be positive")
            if timeout_ms is None:
                timeout_ms = TURN_TIMEOUT_MS
            require_finite(timeout_ms, "timeout")
            if timeout_ms <= 0:
                raise ValueError("timeout must be positive")
            timer = self.stopwatch()
            settled_since = None
            while True:
                now_ms = timer.time()
                error = wrap_deg(heading_deg - require_finite(self.imu.heading(), "heading"))
                if abs(error) <= TURN_TOLERANCE_DEG:
                    if settled_since is None:
                        settled_since = now_ms
                    if now_ms - settled_since >= TURN_SETTLE_MS:
                        break
                    turn_rate = 0.0
                else:
                    settled_since = None
                    turn_rate = clamp(
                        kp * error + (MIN_TURN_RATE_DPS if error > 0 else -MIN_TURN_RATE_DPS),
                        MAX_TURN_RATE_DPS,
                    )
                if now_ms >= timeout_ms:
                    raise RuntimeError("alignment timed out; gyro or turn direction needs checking")
                self.drive.drive(0, turn_rate)
                self.wait(LOOP_MS)
        finally:
            self.drive.brake()

    def curve(self, heading_deg, speed_mm_s, turn_rate_dps, timeout_ms=None):
        try:
            for value in (heading_deg, speed_mm_s, turn_rate_dps):
                require_finite(value, "curve argument")
            self.target_heading_deg = heading_deg
            if speed_mm_s == 0 or turn_rate_dps == 0:
                raise ValueError("curve speed and turn rate must be nonzero")
            rate_limit = min(abs(turn_rate_dps), MAX_TURN_RATE_DPS)
            first_error = wrap_deg(heading_deg - self.imu.heading())
            if timeout_ms is None:
                timeout_ms = MOVE_TIMEOUT_MARGIN_MS + (
                    MOVE_TIMEOUT_FACTOR * abs(first_error) / rate_limit * 1000.0
                )
            require_finite(timeout_ms, "timeout")
            if timeout_ms <= 0:
                raise ValueError("timeout must be positive")
            timer = self.stopwatch()
            direction = 1 if speed_mm_s > 0 else -1
            while True:
                error = wrap_deg(heading_deg - require_finite(self.imu.heading(), "heading"))
                if abs(error) <= CURVE_TOLERANCE_DEG:
                    break
                if timer.time() >= timeout_ms:
                    raise RuntimeError("curve timed out; check turn direction and gyro")
                fraction = min(1.0, abs(error) / CURVE_SLOWDOWN_DEG)
                speed = min(abs(speed_mm_s), max(MIN_DRIVE_SPEED_MM_S, fraction * abs(speed_mm_s)))
                rate = rate_limit if error > 0 else -rate_limit
                self.drive.drive(direction * speed, rate)
                self.wait(LOOP_MS)
        finally:
            self.drive.brake()

hub = None
motors = None
modull = None
modulr = None
_motion = None
_wait = None

def configure(hub_device, drive_base, left_attachment, right_attachment,
              wait_function, stopwatch_factory):
    global hub, motors, modull, modulr, _motion, _wait
    hub, motors = hub_device, drive_base
    modull, modulr = left_attachment, right_attachment
    _wait = wait_function
    _motion = Motion(hub.imu, motors, wait_function, stopwatch_factory)

def setup_hardware():

    from pybricks.hubs import PrimeHub
    from pybricks.parameters import Axis, Button, Color, Direction, Port
    from pybricks.pupdevices import Motor
    from pybricks.robotics import DriveBase
    from pybricks.tools import StopWatch
    from pybricks.tools import wait as hub_wait

    hub_device = PrimeHub(top_side=Axis.Z, front_side=Axis.Y)
    hub_device.light.on(Color.MAGENTA)
    hub_device.system.set_stop_button(Button.BLUETOOTH)
    left_direction = (Direction.COUNTERCLOCKWISE if GUESS_LEFT_FORWARD_IS_CCW
                      else Direction.CLOCKWISE)
    right_direction = (Direction.COUNTERCLOCKWISE if GUESS_RIGHT_FORWARD_IS_CCW
                       else Direction.CLOCKWISE)
    left = Motor(getattr(Port, LEFT_PORT), left_direction)
    right = Motor(getattr(Port, RIGHT_PORT), right_direction)
    left_attachment = Motor(getattr(Port, LEFT_MODULE_PORT), Direction.CLOCKWISE)
    right_attachment = Motor(getattr(Port, RIGHT_MODULE_PORT), Direction.CLOCKWISE)
    left_attachment.control.stall_tolerances(MODULE_STALL_SPEED_DPS, MODULE_STALL_TIME_MS)
    drive = DriveBase(left, right, WHEEL_DIAMETER_MM, AXLE_TRACK_MM)

    drive.use_gyro(False)
    configure(hub_device, drive, left_attachment, right_attachment, hub_wait, StopWatch)
    timer = StopWatch()
    try:
        while not hub.imu.ready():
            if timer.time() >= IMU_READY_TIMEOUT_MS:
                raise RuntimeError("IMU not ready; place the robot flat and stationary")
            wait(LOOP_MS)
        hub.imu.reset_heading(0)
    except BaseException:
        stop_all()
        raise

def wait(time_ms):
    if _wait is None:
        raise RuntimeError("call setup_hardware() or configure() first")
    _wait(time_ms)

def motors_pid(stp, speed, amount):
    if _motion is None:
        raise RuntimeError("call setup_hardware() or configure() first")
    _motion.drive_heading(stp, speed, amount)

def ausrichten1(stp):
    _motion.align(stp, TURN_SLOW_KP)

def ausrichten2(stp):
    _motion.align(stp, TURN_FAST_KP)

def motors_kurve1(target_angle, speed, steering):
    _motion.curve(target_angle, speed, steering)

def timed_straight(motor_speed_dps, duration_ms):
    speed_mm_s = motor_speed_dps * pi * WHEEL_DIAMETER_MM / 360.0
    try:
        motors.drive(speed_mm_s, 0)
        wait(duration_ms)
    finally:
        motors.brake()

def stop_all():

    try:
        if motors is not None:
            motors.brake()
    finally:
        try:
            if modull is not None:
                modull.stop()
        finally:
            if modulr is not None:
                modulr.stop()

def wait_for_start():
    from pybricks.parameters import Button
    motors.brake()
    for button in (Button.RIGHT, Button.LEFT):
        while button in hub.buttons.pressed():
            wait(LOOP_MS)
        while button not in hub.buttons.pressed():
            wait(LOOP_MS)
        while button in hub.buttons.pressed():
            wait(LOOP_MS)

def demo():
    motors_pid(0, 300, 20)
    ausrichten2(90)
    motors_pid(90, 300, 20)
    motors_pid(90, -200, 20)
    stop_all()

def mission():
    demo()

def main():
    setup_hardware()
    try:
        mission()
    finally:
        stop_all()

if __name__ == "__main__":
    main()
