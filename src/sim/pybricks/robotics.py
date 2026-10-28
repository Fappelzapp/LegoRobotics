"""Stub of ``pybricks.robotics``.

Tracks synthetic distance and angle. It does not move anything and does not
model acceleration, slip, or sensor behaviour.
"""

from .parameters import Stop


class DriveBase:
    def __init__(self, left_motor, right_motor, wheel_diameter, axle_track):
        self.left_motor = left_motor
        self.right_motor = right_motor
        self.wheel_diameter = wheel_diameter
        self.axle_track = axle_track
        self._distance = 0.0
        self._angle = 0.0
        self._use_gyro = False
        self.settings_values = {}

    def use_gyro(self, use_gyro):
        self._use_gyro = bool(use_gyro)

    def settings(
        self,
        straight_speed=None,
        straight_acceleration=None,
        turn_rate=None,
        turn_acceleration=None,
    ):
        self.settings_values = {
            "straight_speed": straight_speed,
            "straight_acceleration": straight_acceleration,
            "turn_rate": turn_rate,
            "turn_acceleration": turn_acceleration,
        }

    def straight(self, distance, then=Stop.HOLD, wait=True):
        self._distance += distance

    def turn(self, angle, then=Stop.HOLD, wait=True, absolute=False):
        if absolute:
            self._angle = angle
        else:
            self._angle += angle

    def drive(self, speed, turn_rate):
        return None

    def stop(self, then=Stop.HOLD):
        return None

    def distance(self):
        return self._distance

    def angle(self):
        return self._angle

    def state(self):
        return (self._distance, 0, self._angle, 0)

    def reset(self, distance=0, angle=0):
        self._distance = distance
        self._angle = angle
