"""Small deterministic backend for the SAME PID.py mission/control functions.

This is NOT Pybricks firmware emulation. wait(ms) advances a virtual clock, not
wall time. The drive model is planar kinematics plus explicitly assumed lags.
No USB, BLE, real motors, GUI packages, or third-party dependencies are used.
"""

from math import ceil, cos, exp, isfinite, pi, radians, sin

from lib.geometry import wrap_deg


class VirtualStopWatch:
    def __init__(self, world):
        self.world = world
        self.start = world.time_ms

    def time(self):
        return self.world.time_ms - self.start

    def reset(self):
        self.start = self.world.time_ms


class SimIMU:
    def __init__(self, world):
        self.world = world
        self.offset = 0.0
        self.reset_time_ms = 0

    def heading(self):
        drift = self.world.gyro_drift_dps * (self.world.time_ms - self.reset_time_ms) / 1000.0
        return self.world.heading_deg - self.offset + drift

    def reset_heading(self, angle):
        self.offset = self.world.heading_deg - angle
        self.reset_time_ms = self.world.time_ms


class SimDriveBase:
    def __init__(self, world):
        self.world = world
        self.speed_command = 0.0
        self.turn_command = 0.0
        self.odometry_mm = 0.0
        self.brake_count = 0
        self.commands = []

    def drive(self, speed, turn_rate):
        if not isfinite(speed) or not isfinite(turn_rate):
            raise ValueError("simulator command must be finite")
        self.speed_command, self.turn_command = speed, turn_rate
        self.commands.append((speed, turn_rate))

    def distance(self):
        return self.odometry_mm

    def brake(self):
        self.speed_command = self.turn_command = 0.0
        # Idealised instantaneous brake. Real braking distance must be measured.
        self.world.speed_mm_s = self.world.turn_rate_dps = 0.0
        self.brake_count += 1
        self.world.record()


class SimModule:
    """Angles and wait=False scheduling only; no attachment contact physics."""

    def __init__(self, world):
        self.world = world
        self._angle = 0.0
        self.target = None
        self.rate = 0.0

    def angle(self):
        return self._angle

    def run_angle(self, speed, angle, wait=True):
        if not isfinite(speed) or not isfinite(angle):
            raise ValueError("module command must be finite")
        if angle == 0 or speed == 0:
            self.stop()
            return
        # Firmware pbio_servo_run_angle: the signs MULTIPLY. This differs from
        # run_target(), where speed's sign is ignored. Preserve both signs.
        rotation = angle if speed > 0 else -angle
        self.target = self._angle + rotation
        self.rate = abs(speed) if rotation > 0 else -abs(speed)
        if wait:
            self.world.wait(ceil(abs(angle / speed) * 1000.0))

    def run_until_stalled(self, speed, duty_limit):
        if self.world.assume_stall_ms is None:
            raise NotImplementedError(
                "route 5 needs attachment contact physics; explicitly pass --assume-stall-ms to use a timing assumption"
            )
        self.target = None
        self.rate = speed
        self.world.assumptions.add(
            "Attachment stall is assumed after %d ms; NOT collision/contact simulation."
            % self.world.assume_stall_ms
        )
        self.world.wait(self.world.assume_stall_ms)
        self.stop()
        return self._angle

    def stop(self):
        self.target = None
        self.rate = 0.0

    def advance(self, dt):
        if self.rate == 0:
            return
        change = self.rate * dt
        if self.target is not None and abs(change) >= abs(self.target - self._angle):
            self._angle = self.target
            self.stop()
        else:
            self._angle += change


class _Speaker:
    def beep(self, frequency):
        # Deliberate no-op; audio duration is not simulated.
        return None


class _Hub:
    def __init__(self, world):
        self.imu = SimIMU(world)
        self.speaker = _Speaker()


class Simulation:
    def __init__(self, heading_deg=0.0, turn_lag_s=0.12, speed_lag_s=0.08,
                 drift_dps=0.0, slip_fraction=0.0, blocked=False,
                 assume_stall_ms=None, max_time_ms=600000):
        for value in (heading_deg, turn_lag_s, speed_lag_s, drift_dps, slip_fraction):
            if not isfinite(value):
                raise ValueError("simulation settings must be finite")
        if turn_lag_s < 0 or speed_lag_s < 0 or not 0 <= slip_fraction <= 1:
            raise ValueError("lags must be non-negative; slip must be between 0 and 1")
        if assume_stall_ms is not None and (not isfinite(assume_stall_ms) or assume_stall_ms <= 0):
            raise ValueError("assumed stall time must be positive and finite")
        self.time_ms = 0
        self.x_mm = self.y_mm = 0.0
        self.heading_deg = heading_deg
        self.speed_mm_s = self.turn_rate_dps = 0.0
        self.turn_lag_s, self.speed_lag_s = turn_lag_s, speed_lag_s
        self.gyro_drift_dps = drift_dps
        self.slip_fraction = slip_fraction
        self.blocked = blocked
        self.assume_stall_ms = assume_stall_ms
        self.max_time_ms = max_time_ms
        self.hub = _Hub(self)
        self.drive = SimDriveBase(self)
        self.left_module = SimModule(self)
        self.right_module = SimModule(self)
        self.samples = []
        self.motion = None
        self.assumptions = {
            "2D model; no field obstacles, tyre forces, backlash, battery, or ramp model.",
            "Speed/turn lags are illustrative assumptions, not measured robot data.",
            "Brake is instantaneous in this model; hardware can overshoot.",
            "Motor polarity and DriveBase API are assumed correct, not firmware-tested.",
            "Module angles use constant speed; beep duration is ignored.",
        }

    def stopwatch(self):
        return VirtualStopWatch(self)

    def connect(self, program):
        program.configure(self.hub, self.drive, self.left_module, self.right_module,
                          self.wait, self.stopwatch)
        self.motion = program._motion
        self.record()

    def wait(self, duration_ms):
        if not isfinite(duration_ms) or duration_ms < 0:
            raise ValueError("wait duration must be finite and non-negative")
        remaining = int(ceil(duration_ms))
        if self.time_ms + remaining > self.max_time_ms:
            raise RuntimeError("simulation virtual-time budget exceeded")
        while remaining:
            # At most 20 ms per integration step; no real sleeping, even for a
            # source wait(1000). This also advances wait=False attachment moves.
            step_ms = min(20, remaining)
            dt = step_ms / 1000.0
            speed_target = 0.0 if self.blocked else self.drive.speed_command
            turn_target = 0.0 if self.blocked else self.drive.turn_command
            v_mix = 1.0 if self.speed_lag_s == 0 else 1.0 - exp(-dt / self.speed_lag_s)
            w_mix = 1.0 if self.turn_lag_s == 0 else 1.0 - exp(-dt / self.turn_lag_s)
            self.speed_mm_s += (speed_target - self.speed_mm_s) * v_mix
            self.turn_rate_dps += (turn_target - self.turn_rate_dps) * w_mix
            wheel_travel = self.speed_mm_s * dt
            ground_travel = wheel_travel * (1.0 - self.slip_fraction)
            angle_change = self.turn_rate_dps * dt
            theta = radians(self.heading_deg)
            delta = radians(angle_change)
            # Exact constant-twist arc over this integration step.
            if abs(delta) < 1e-12:
                self.x_mm += ground_travel * cos(theta)
                self.y_mm += ground_travel * sin(theta)
            else:
                radius = ground_travel / delta
                self.x_mm += radius * (sin(theta + delta) - sin(theta))
                self.y_mm -= radius * (cos(theta + delta) - cos(theta))
            self.heading_deg += angle_change
            # Encoders count wheel travel even when the floor distance is less.
            self.drive.odometry_mm += wheel_travel
            self.left_module.advance(dt)
            self.right_module.advance(dt)
            self.time_ms += step_ms
            remaining -= step_ms
            self.record()

    def record(self):
        target = getattr(self.motion, "target_heading_deg", None)
        heading = self.hub.imu.heading()
        self.samples.append({
            "time_s": self.time_ms / 1000.0,
            "x_mm": self.x_mm, "y_mm": self.y_mm,
            "heading_deg": heading, "world_heading_deg": self.heading_deg,
            "target_deg": target,
            "error_deg": None if target is None else wrap_deg(target - heading),
            "encoder_mm": self.drive.odometry_mm,
            "speed_command_mm_s": self.drive.speed_command,
            "turn_command_deg_s": self.drive.turn_command,
            "speed_mm_s": self.speed_mm_s, "turn_rate_deg_s": self.turn_rate_dps,
            "left_module_deg": self.left_module.angle(),
            "right_module_deg": self.right_module.angle(),
        })
