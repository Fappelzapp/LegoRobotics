"""Stub of ``pybricks.hubs``."""

from .parameters import Axis


class _Speaker:
    def beep(self, frequency=500, duration=100, volume=100):
        return None


class _Light:
    def on(self, color):
        return None

    def off(self):
        return None


class _Display:
    def text(self, text):
        return None

    def char(self, char):
        return None

    def icon(self, icon):
        return None


class _IMU:
    def __init__(self):
        self._heading = 0.0

    def heading(self):
        return self._heading

    def reset_heading(self, angle=0):
        self._heading = angle

    def tilt(self):
        return (0.0, 0.0)

    def angular_velocity(self, axis=Axis.Z):
        return 0.0

    def acceleration(self, axis=None, calibrated=True):
        if axis is None:
            return (0.0, 0.0, -9810.0)
        return 0.0

    def rotation(self, axis=Axis.Z, calibrated=True):
        return 0.0


class PrimeHub:
    def __init__(self, top_side=Axis.Z, front_side=Axis.X):
        self.top_side = top_side
        self.front_side = front_side
        self.speaker = _Speaker()
        self.light = _Light()
        self.display = _Display()
        self.imu = _IMU()


class InventorHub(PrimeHub):
    pass


class EssentialHub(PrimeHub):
    pass


class TechnicHub(PrimeHub):
    pass
