"""Competition motion loops shared by the hub and deterministic laptop backend.

No Pybricks imports. imu, drive, wait, and stopwatch are supplied by the caller.
Units: millimetres, seconds, body degrees; clockwise heading / turn rate positive.
"""

from math import isfinite, sqrt

from lib import competition_config as config
from lib.geometry import wrap_deg


def clamp(value, limit):
    return max(-limit, min(limit, value))


def require_finite(value, name):
    if not isfinite(value):
        raise ValueError(name + " must be finite")
    return value


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
    def __init__(self, imu, drive, wait, stopwatch, settings=config):
        self.imu = imu
        self.drive = drive
        self.wait = wait
        self.stopwatch = stopwatch
        self.settings = settings
        self.target_heading_deg = None  # read-only telemetry for the laptop recorder
        self.heading_pid = HeadingPID(
            settings.HEADING_KP, settings.HEADING_KI, settings.HEADING_KD,
            settings.MAX_TURN_RATE_DPS, settings.INTEGRAL_LIMIT_DEG_S,
        )

    def drive_heading(self, heading_deg, speed_mm_s, distance_cm, timeout_ms=None):
        """Drive signed speed for a non-negative distance; brake on EVERY exit.

        Mission arguments remain centimetres. Odometry and all internal maths
        are millimetres. There is deliberately no encoder/gyro reset here: use a
        distance baseline so adjacent moves do not change the heading reference.
        """
        cfg = self.settings
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
                timeout_ms = cfg.MOVE_TIMEOUT_MARGIN_MS + (
                    cfg.MOVE_TIMEOUT_FACTOR * target_mm / requested * 1000.0
                )
            require_finite(timeout_ms, "timeout")
            if timeout_ms <= 0:
                raise ValueError("timeout must be positive")
            timer = self.stopwatch()
            previous_ms = -cfg.LOOP_MS
            speed = 0.0
            self.heading_pid.reset()

            while True:
                now_ms = timer.time()
                travelled = direction * (
                    require_finite(self.drive.distance(), "odometry") - baseline
                )
                remaining = target_mm - travelled
                if remaining <= cfg.DISTANCE_TOLERANCE_MM:
                    break
                if now_ms >= timeout_ms:
                    raise RuntimeError("heading move timed out; check encoders, polarity, or a blocked robot")
                dt = (now_ms - previous_ms) / 1000.0
                previous_ms = now_ms
                turn_rate = self.heading_pid.update(heading_deg, self.imu.heading(), dt)
                # v^2 = 2*a*d: taper requested speed before the endpoint. The
                # floor avoids an asymptotic crawl; brake supplies the final stop.
                braking_speed = sqrt(2.0 * cfg.DECELERATION_MM_S2 * max(remaining, 0.0))
                speed = min(requested, speed + cfg.ACCELERATION_MM_S2 * dt, braking_speed)
                speed = max(min(requested, cfg.MIN_DRIVE_SPEED_MM_S), speed)
                # Pybricks: speed FIRST (mm/s), body turn rate SECOND (deg/s).
                # Body heading correction does not flip when reversing.
                self.drive.drive(direction * speed, turn_rate)
                self.wait(cfg.LOOP_MS)
        finally:
            self.drive.brake()

    def align(self, heading_deg, kp, timeout_ms=None):
        """Shortest-path absolute turn, with tolerance, settling, and a timeout."""
        cfg = self.settings
        try:
            self.target_heading_deg = require_finite(heading_deg, "heading")
            require_finite(kp, "turn gain")
            if kp <= 0:
                raise ValueError("turn gain must be positive")
            if timeout_ms is None:
                timeout_ms = cfg.TURN_TIMEOUT_MS
            require_finite(timeout_ms, "timeout")
            if timeout_ms <= 0:
                raise ValueError("timeout must be positive")
            timer = self.stopwatch()
            settled_since = None
            while True:
                now_ms = timer.time()
                error = wrap_deg(heading_deg - require_finite(self.imu.heading(), "heading"))
                if abs(error) <= cfg.TURN_TOLERANCE_DEG:
                    if settled_since is None:
                        settled_since = now_ms
                    if now_ms - settled_since >= cfg.TURN_SETTLE_MS:
                        break
                    turn_rate = 0.0
                else:
                    settled_since = None
                    turn_rate = clamp(
                        kp * error + (cfg.MIN_TURN_RATE_DPS if error > 0 else -cfg.MIN_TURN_RATE_DPS),
                        cfg.MAX_TURN_RATE_DPS,
                    )
                if now_ms >= timeout_ms:
                    raise RuntimeError("alignment timed out; gyro or turn direction needs checking")
                self.drive.drive(0, turn_rate)
                self.wait(cfg.LOOP_MS)
        finally:
            self.drive.brake()

    def curve(self, heading_deg, speed_mm_s, turn_rate_dps, timeout_ms=None):
        """Curve to an absolute heading. The target chooses the turning direction.

        turn_rate_dps is a magnitude, NOT a steering percentage. Reverse changes
        travel direction only. If the target is overshot, the turn reverses.
        """
        cfg = self.settings
        try:
            for value in (heading_deg, speed_mm_s, turn_rate_dps):
                require_finite(value, "curve argument")
            self.target_heading_deg = heading_deg
            if speed_mm_s == 0 or turn_rate_dps == 0:
                raise ValueError("curve speed and turn rate must be nonzero")
            rate_limit = min(abs(turn_rate_dps), cfg.MAX_TURN_RATE_DPS)
            first_error = wrap_deg(heading_deg - self.imu.heading())
            if timeout_ms is None:
                timeout_ms = cfg.MOVE_TIMEOUT_MARGIN_MS + (
                    cfg.MOVE_TIMEOUT_FACTOR * abs(first_error) / rate_limit * 1000.0
                )
            require_finite(timeout_ms, "timeout")
            if timeout_ms <= 0:
                raise ValueError("timeout must be positive")
            timer = self.stopwatch()
            direction = 1 if speed_mm_s > 0 else -1
            while True:
                error = wrap_deg(heading_deg - require_finite(self.imu.heading(), "heading"))
                if abs(error) <= cfg.CURVE_TOLERANCE_DEG:
                    break
                if timer.time() >= timeout_ms:
                    raise RuntimeError("curve timed out; check turn direction and gyro")
                fraction = min(1.0, abs(error) / cfg.CURVE_SLOWDOWN_DEG)
                speed = min(abs(speed_mm_s), max(cfg.MIN_DRIVE_SPEED_MM_S, fraction * abs(speed_mm_s)))
                rate = rate_limit if error > 0 else -rate_limit
                self.drive.drive(direction * speed, rate)
                self.wait(cfg.LOOP_MS)
        finally:
            self.drive.brake()
