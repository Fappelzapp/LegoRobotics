# pyright: reportOptionalMemberAccess=false
"""PID - a one-file Pybricks kit for building your own missions.

WHAT THIS IS
  A reusable base for a two-wheel drivetrain with a gyro. It contains no
  mission for any particular match: the bottom of this file is a blank page
  for you to write in.

WHY ONE FILE
  Pybricks Code uploads one program. This file IS that program. It imports
  nothing of ours, so there is no lib folder to copy and no second file to
  forget.

START A NEW PROJECT
  1. Paste this whole file into a new Pybricks Code program and name it.
  2. Edit the SETTINGS block. Ports and wheel diameter are the only must-dos.
  3. Write your route inside mission() at the bottom.
  4. Press Run. It starts immediately.
  5. Wheels raised first: confirm forward and clockwise before trusting it.

THE COMMANDS YOU WILL ACTUALLY USE
  motors_pid(heading, speed, distance_cm)
      Drive, holding a heading. speed is mm/s, positive = forward.
      distance is centimetres.
        motors_pid(0, 400, 50)      straight 50 cm, holding 0 deg
        motors_pid(-90, -300, 20)   reverse 20 cm, holding -90 deg
  ausrichten1(heading) / ausrichten2(heading)
      Turn to an absolute heading by the shortest path. 1 = gentle, 2 = fast.
  motors_kurve1(heading, speed, turn_rate)
      Travel while turning, until the heading is reached.
  timed_straight(motor_speed_dps, ms)
      Drive straight for a fixed time. For "push until something happens".
  stop_all()
      Brake the wheels and stop both attachments. Also used on errors.

UNITS - these are NOT interchangeable
  heading            degrees, absolute, clockwise positive
  speed              millimetres per second
  distance           centimetres
  turn_rate          body degrees per second, NOT a percentage
  attachment angles  motor degrees

ABOUT THE SETTINGS NUMBERS
  "source"   copied from the team's competition paste - NOT measured
  "proposal" an unverified guess: safe, but not tuned
  Nothing here was tuned on a hub. Motor polarity is an inference, not an
  observation. Verify with the wheels raised before a competition run.
"""

from math import isfinite, pi, sqrt

# =====================================================================
# SETTINGS - edit here
#
# "source" values were copied from the competition paste; that is NOT the
# same as measured. "proposal" values are unverified guesses that should be
# checked on the robot. Nothing below was tuned on a hub.
# =====================================================================

WHEEL_DIAMETER_MM = 49.5  # MEASURED 2026-11-04 (user report). Was 62.4 (source, unmeasured).
AXLE_TRACK_MM = 80.0  # MEASURED 2026-11-04 (user report). Was 106.0 (source, unmeasured).
LEFT_PORT = "E"  # source: links
RIGHT_PORT = "A"  # source: rechts
LEFT_MODULE_PORT = "F"  # source: modull
RIGHT_MODULE_PORT = "B"  # source: modulr

# Inference from the original timed straight moves: links.run(-v), rechts.run(v).
# Confirm with wheels raised BEFORE running a mission. Not a hardware observation.
GUESS_LEFT_FORWARD_IS_CCW = True
GUESS_RIGHT_FORWARD_IS_CCW = False

LOOP_MS = 20  # user-requested wait; real dt includes work done between waits
HEADING_KP = 4.0  # source gain, now outputs body turn rate in deg/s
HEADING_KI = 0.0  # source: disabled
# Source kd=1 multiplied a per-pass difference. At a nominal 20 ms, 1*0.020
# gives equivalent continuous-time scaling (seconds). Derived, NOT retuned.
HEADING_KD = 1.0 * LOOP_MS / 1000.0
INTEGRAL_LIMIT_DEG_S = 30.0  # proposal: bounds accumulated error, not motor power
MAX_TURN_RATE_DPS = 180.0  # proposal: safety cap; not a measured motor limit

ACCELERATION_MM_S2 = 600.0  # proposal: replaces the iteration-count speed ramp
DECELERATION_MM_S2 = 600.0  # proposal: stopping-distance envelope, not a guarantee
MIN_DRIVE_SPEED_MM_S = 50.0  # source curve floor, proposed for straight moves too
DISTANCE_TOLERANCE_MM = 1.0  # proposal: encoder-distance completion tolerance
TURN_TOLERANCE_DEG = 2.0  # proposal: replaces exact integer equality
TURN_SETTLE_MS = 100  # proposal: require several in-tolerance readings
CURVE_TOLERANCE_DEG = 3.0  # source: motors_kurve1
CURVE_SLOWDOWN_DEG = 10.0  # source: last 10 degrees

# Source turn gains (motor deg/s per heading degree) converted to BODY deg/s
# under the inferred direct-drive geometry. These are NOT the same unit as kp.
MOTOR_TO_BODY_TURN = WHEEL_DIAMETER_MM / AXLE_TRACK_MM
TURN_SLOW_KP = 3.0 * MOTOR_TO_BODY_TURN  # derived from ausrichten1
TURN_FAST_KP = 5.0 * MOTOR_TO_BODY_TURN  # derived from ausrichten2
MIN_TURN_RATE_DPS = 30.0 * MOTOR_TO_BODY_TURN  # source +/-30 motor-deg/s kick
TURN_TIMEOUT_MS = 10000  # proposal: fail rather than spin indefinitely
MOVE_TIMEOUT_MARGIN_MS = 3000  # proposal: allowances for acceleration / lag
MOVE_TIMEOUT_FACTOR = 4.0  # proposal: multiple of nominal travel time
IMU_READY_TIMEOUT_MS = 10000  # proposal: calibrate stationary before a mission

MODULE_STALL_SPEED_DPS = 300  # source: modull.control.stall_tolerances
MODULE_STALL_TIME_MS = 50  # source


# =====================================================================
# SMALL HELPERS
# =====================================================================

def wrap_deg(angle_deg):
    """Normalise an angle to (-180, 180]."""
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


# =====================================================================
# PID - the control loop
# =====================================================================

class HeadingPID:
    """Wrapped heading error, derivative on measurement, bounded integral/output."""

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
        # Do not integrate further into saturation, but allow it to unwind.
        if output == raw or error * raw <= 0:
            self.integral = candidate
        return output


class Motion:
    """Drive, align, and curve primitives. Works on a hub or in the laptop model."""

    def __init__(self, imu, drive, wait, stopwatch):
        self.imu = imu
        self.drive = drive
        self.wait = wait
        self.stopwatch = stopwatch
        self.target_heading_deg = None  # read-only telemetry for the laptop recorder
        self.heading_pid = HeadingPID(
            HEADING_KP, HEADING_KI, HEADING_KD, MAX_TURN_RATE_DPS, INTEGRAL_LIMIT_DEG_S,
        )

    def drive_heading(self, heading_deg, speed_mm_s, distance_cm, timeout_ms=None):
        """Drive signed speed for a non-negative distance; brake on EVERY exit.

        Mission arguments remain centimetres. Odometry and all internal maths
        are millimetres. There is deliberately no encoder/gyro reset here: use a
        distance baseline so adjacent moves do not change the heading reference.
        """
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
                # v^2 = 2*a*d: taper requested speed before the endpoint. The
                # floor avoids an asymptotic crawl; brake supplies the final stop.
                braking_speed = sqrt(2.0 * DECELERATION_MM_S2 * max(remaining, 0.0))
                speed = min(requested, speed + ACCELERATION_MM_S2 * dt, braking_speed)
                speed = max(min(requested, MIN_DRIVE_SPEED_MM_S), speed)
                # Pybricks: speed FIRST (mm/s), body turn rate SECOND (deg/s).
                # Body heading correction does not flip when reversing.
                self.drive.drive(direction * speed, turn_rate)
                self.wait(LOOP_MS)
        finally:
            self.drive.brake()

    def align(self, heading_deg, kp, timeout_ms=None):
        """Shortest-path absolute turn, with tolerance, settling, and a timeout."""
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
        """Curve to an absolute heading. The target chooses the turning direction.

        turn_rate_dps is a magnitude, NOT a steering percentage. Reverse changes
        travel direction only. If the target is overshot, the turn reverses.
        """
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



# =====================================================================

hub = None
motors = None
modull = None
modulr = None
_motion = None
_wait = None


def configure(hub_device, drive_base, left_attachment, right_attachment,
              wait_function, stopwatch_factory):
    """Connect the same control/mission code to real OR simulated devices."""
    global hub, motors, modull, modulr, _motion, _wait
    hub, motors = hub_device, drive_base
    modull, modulr = left_attachment, right_attachment
    _wait = wait_function
    _motion = Motion(hub.imu, motors, wait_function, stopwatch_factory)


def setup_hardware():
    # Deliberately lazy: importing PID must never connect to or move a robot.
    from pybricks.hubs import PrimeHub
    from pybricks.parameters import Axis, Button, Color, Direction, Port
    from pybricks.pupdevices import Motor
    from pybricks.robotics import DriveBase
    from pybricks.tools import StopWatch
    from pybricks.tools import wait as hub_wait

    hub_device = PrimeHub(top_side=Axis.Z, front_side=Axis.Y)  # pyright: ignore[reportArgumentType]
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
    # The custom outer loop owns gyro heading. DriveBase still controls wheel
    # speed internally; we are NOT trying to disable those motor-speed loops.
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


# =====================================================================

def motors_pid(stp, speed, amount):
    """Hold heading stp (deg); signed speed (mm/s); distance amount (cm)."""
    if _motion is None:
        raise RuntimeError("call setup_hardware() or configure() first")
    _motion.drive_heading(stp, speed, amount)


def ausrichten1(stp):
    """Gentler shortest-path turn to absolute heading stp (deg)."""
    _motion.align(stp, TURN_SLOW_KP)


def ausrichten2(stp):
    """Faster shortest-path turn to absolute heading stp (deg)."""
    _motion.align(stp, TURN_FAST_KP)


def motors_kurve1(target_angle, speed, steering):
    """Curve to absolute heading; steering is a TURN RATE in deg/s, not %."""
    _motion.curve(target_angle, speed, steering)


def timed_straight(motor_speed_dps, duration_ms):
    """Replace the two busy-loop raw-motor moves without changing their units.

    Their opposite raw motor signs imply straight travel, NOT an in-place spin.
    After normalising motor directions, one DriveBase command drives both sides.
    Conversion assumes the source direct drive (no unreported gearing).
    """
    speed_mm_s = motor_speed_dps * pi * WHEEL_DIAMETER_MM / 360.0
    try:
        motors.drive(speed_mm_s, 0)
        wait(duration_ms)
    finally:
        motors.brake()


def stop_all():
    # A disconnected device must not prevent attempts to stop the other ones.
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


# =====================================================================


def wait_for_start():
    """Block until the user presses RIGHT, then LEFT. Fresh presses only."""
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
    """A working example to copy from: straight, turn, straight, reverse."""
    motors_pid(0, 300, 20)      # straight 20 cm, holding heading 0
    ausrichten2(90)            # fast turn to heading 90 (shortest path)
    motors_pid(90, 300, 20)    # straight 20 cm, holding heading 90
    motors_pid(90, -200, 20)   # reverse 20 cm, still holding heading 90
    stop_all()


def mission():
    """Replace this body with your own route. Add more functions if you like."""
    demo()


def main():
    setup_hardware()
    try:
        mission()
    finally:
        stop_all()


if __name__ == "__main__":
    main()
