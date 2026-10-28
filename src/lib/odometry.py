"""Differential-drive odometry.

Pure Python. Feed it wheel travel increments in millimetres and optionally an
absolute gyro heading; it maintains a pose.

Conventions match PyBricks: +X forward, +Y right, heading positive clockwise.
"""

import math
from dataclasses import dataclass

from .geometry import arc_pose, wrap_deg


@dataclass
class Pose:
    x_mm: float = 0.0
    y_mm: float = 0.0
    theta_deg: float = 0.0


class Odometry:
    def __init__(self, axle_track_mm, start_pose=None):
        if axle_track_mm <= 0:
            raise ValueError("axle_track_mm must be positive")
        self.axle_track_mm = axle_track_mm
        self._pose = start_pose if start_pose is not None else Pose()
        self._last_gyro_deg = None

    def reset(self, pose=None):
        self._pose = pose if pose is not None else Pose()
        self._last_gyro_deg = None

    def pose(self):
        return Pose(self._pose.x_mm, self._pose.y_mm, self._pose.theta_deg)

    def update(self, left_mm, right_mm, gyro_deg=None):
        """Advance the pose by one step.

        ``left_mm`` and ``right_mm`` are increments since the previous call, not
        cumulative readings.

        If ``gyro_deg`` is given it overrides encoder-based heading; pass the
        absolute gyro heading (for example ``hub.imu.heading()``).
        """
        if gyro_deg is not None:
            if self._last_gyro_deg is None:
                dtheta_deg = 0.0
            else:
                dtheta_deg = wrap_deg(gyro_deg - self._last_gyro_deg)
            self._last_gyro_deg = gyro_deg
        else:
            dtheta_deg = math.degrees(
                (left_mm - right_mm) / self.axle_track_mm
            )

        distance_mm = (left_mm + right_mm) / 2.0
        x, y, theta = arc_pose(
            self._pose.x_mm,
            self._pose.y_mm,
            self._pose.theta_deg,
            distance_mm,
            dtheta_deg,
        )
        self._pose = Pose(x, y, theta)
        return self.pose()
