"""PID controller for the drive base.

Pure Python: this module must not import ``pybricks`` so it can be tested on a
laptop.

Sign convention matches PyBricks: angles and turn rates are positive clockwise.
The controller itself is unit-agnostic; pass a consistent unit per loop
(millimetres for distance, degrees for heading).
"""


def _clamp(value, limit):
    if limit is None:
        return value
    if value > limit:
        return limit
    if value < -limit:
        return -limit
    return value


class PID:
    """Discrete PID with separate integral and output clamps.

    The derivative is taken on the measurement, not the error, so a step
    change in the target does not cause a derivative kick.
    """

    def __init__(
        self,
        kp,
        ki=0.0,
        kd=0.0,
        output_limit=None,
        i_limit=None,
        deadband=0.0,
    ):
        if output_limit is not None and output_limit <= 0:
            raise ValueError("output_limit must be positive")
        if i_limit is not None and i_limit < 0:
            raise ValueError("i_limit must be non-negative")
        if deadband < 0:
            raise ValueError("deadband must be non-negative")

        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limit = output_limit
        self.i_limit = i_limit
        self.deadband = deadband

        self._integral = 0.0
        self._previous_measurement = None

    def reset(self):
        """Clear the integral and derivative history."""
        self._integral = 0.0
        self._previous_measurement = None

    def update(self, target, measured, dt):
        """Return the control output for one time step.

        ``dt`` is in seconds and must be positive. A non-positive ``dt``
        returns 0.0 instead of dividing by zero.
        """
        if dt <= 0:
            return 0.0

        error = target - measured
        if abs(error) < self.deadband:
            error = 0.0

        self._integral = _clamp(self._integral + error * dt, self.i_limit)

        if self._previous_measurement is None:
            derivative = 0.0
        else:
            derivative = (measured - self._previous_measurement) / dt
        self._previous_measurement = measured

        output = self.kp * error - self.kd * derivative + self.ki * self._integral
        return _clamp(output, self.output_limit)
