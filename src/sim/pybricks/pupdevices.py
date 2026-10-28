"""Stub of ``pybricks.pupdevices``."""

from .parameters import Color, Direction, Stop


class Motor:
    def __init__(self, port, positive_direction=Direction.CLOCKWISE):
        self.port = port
        self.positive_direction = positive_direction
        self._angle = 0.0

    def run(self, speed):
        return None

    def run_time(self, speed, time, then=Stop.HOLD, wait=True):
        # time in milliseconds
        self._angle += speed * time / 1000.0

    def run_angle(self, speed, angle, then=Stop.HOLD, wait=True):
        self._angle += angle

    def run_target(self, speed, target_angle, then=Stop.HOLD, wait=True):
        self._angle = target_angle

    def angle(self):
        return self._angle

    def reset_angle(self, angle=0):
        self._angle = angle

    def stop(self, then=Stop.COAST):
        return None

    def dc(self, duty):
        return None


class ColorSensor:
    def __init__(self, port):
        self.port = port
        self._reflection = 0.0

    def color(self):
        return Color.NONE

    def reflection(self):
        return self._reflection

    def ambient(self):
        return 0.0

    def hsv(self):
        return (0, 0, 0)


class DistanceSensor:
    def __init__(self, port):
        self.port = port
        self._distance = 2000.0

    def distance(self):
        return self._distance


class ForceSensor:
    def __init__(self, port):
        self.port = port
        self._force = 0.0

    def force(self):
        return self._force

    def pressed(self, force=3.0):
        return self._force > force
