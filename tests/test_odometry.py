import math
import unittest

from tests import _path  # noqa: F401
from lib.odometry import Odometry, Pose


class OdometryTests(unittest.TestCase):
    def test_straight_forward(self):
        odo = Odometry(112.0)
        pose = odo.update(100.0, 100.0)
        self.assertAlmostEqual(pose.x_mm, 100.0)
        self.assertAlmostEqual(pose.y_mm, 0.0)
        self.assertAlmostEqual(pose.theta_deg, 0.0)

    def test_turn_right_in_place(self):
        odo = Odometry(112.0)
        half_track_arc = 112.0 * math.pi / 4.0  # gives a 90 deg turn
        pose = odo.update(half_track_arc, -half_track_arc)
        self.assertAlmostEqual(pose.theta_deg, 90.0)
        self.assertAlmostEqual(pose.x_mm, 0.0)
        self.assertAlmostEqual(pose.y_mm, 0.0)

    def test_quarter_arc_turning_right(self):
        odo = Odometry(112.0)
        dtheta = math.pi / 2.0
        left = (100.0 + 56.0) * dtheta
        right = (100.0 - 56.0) * dtheta
        pose = odo.update(left, right)
        self.assertAlmostEqual(pose.theta_deg, 90.0, places=6)
        self.assertAlmostEqual(pose.x_mm, 100.0, places=6)
        self.assertAlmostEqual(pose.y_mm, 100.0, places=6)

    def test_gyro_overrides_encoder_heading(self):
        odo = Odometry(112.0)
        odo.update(0.0, 0.0, gyro_deg=0.0)
        pose = odo.update(0.0, 0.0, gyro_deg=10.0)
        self.assertAlmostEqual(pose.theta_deg, 10.0)

    def test_reset_sets_pose(self):
        odo = Odometry(112.0)
        odo.update(100.0, 100.0)
        odo.reset(Pose(10.0, 20.0, 30.0))
        pose = odo.update(0.0, 0.0)
        self.assertAlmostEqual(pose.x_mm, 10.0)
        self.assertAlmostEqual(pose.y_mm, 20.0)
        self.assertAlmostEqual(pose.theta_deg, 30.0)

    def test_invalid_track(self):
        with self.assertRaises(ValueError):
            Odometry(0.0)


if __name__ == "__main__":
    unittest.main()
