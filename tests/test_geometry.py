import math
import unittest

from tests import _path  # noqa: F401
from lib.geometry import (
    arc_pose,
    mm_per_motor_deg,
    motor_deg_for_mm,
    motor_deg_for_turn,
    wheel_circumference_mm,
    wrap_deg,
)


class GeometryTests(unittest.TestCase):
    def test_circumference(self):
        self.assertAlmostEqual(wheel_circumference_mm(56.0), math.pi * 56.0)

    def test_mm_per_motor_deg(self):
        self.assertAlmostEqual(
            mm_per_motor_deg(56.0, 1.0), math.pi * 56.0 / 360.0
        )

    def test_gear_ratio_reduces_travel_per_motor_degree(self):
        self.assertAlmostEqual(
            mm_per_motor_deg(56.0, 2.0), math.pi * 56.0 / 720.0
        )

    def test_motor_deg_for_mm_round_trip(self):
        degrees = motor_deg_for_mm(100.0, 56.0, 1.0)
        self.assertAlmostEqual(
            degrees * mm_per_motor_deg(56.0, 1.0), 100.0
        )

    def test_turn_motor_degrees(self):
        # 90 deg with a 112 mm track and 56 mm wheels: 180 deg per wheel.
        self.assertAlmostEqual(
            motor_deg_for_turn(90.0, 112.0, 56.0, 1.0), 180.0
        )
        self.assertAlmostEqual(
            motor_deg_for_turn(-90.0, 112.0, 56.0, 1.0), -180.0
        )

    def test_turn_respects_gear_ratio(self):
        self.assertAlmostEqual(
            motor_deg_for_turn(90.0, 112.0, 56.0, 2.0), 90.0
        )

    def test_wrap_deg(self):
        self.assertAlmostEqual(wrap_deg(0.0), 0.0)
        self.assertAlmostEqual(wrap_deg(180.0), 180.0)
        self.assertAlmostEqual(wrap_deg(-180.0), 180.0)
        self.assertAlmostEqual(wrap_deg(190.0), -170.0)
        self.assertAlmostEqual(wrap_deg(360.0), 0.0)
        self.assertAlmostEqual(wrap_deg(-370.0), -10.0)

    def test_arc_straight(self):
        x, y, theta = arc_pose(0.0, 0.0, 0.0, 100.0, 0.0)
        self.assertAlmostEqual(x, 100.0)
        self.assertAlmostEqual(y, 0.0)
        self.assertAlmostEqual(theta, 0.0)

    def test_arc_pure_rotation_does_not_translate(self):
        x, y, theta = arc_pose(5.0, 7.0, 0.0, 0.0, 90.0)
        self.assertAlmostEqual(x, 5.0)
        self.assertAlmostEqual(y, 7.0)
        self.assertAlmostEqual(theta, 90.0)

    def test_arc_quarter_circle_turning_right(self):
        # Radius 100 mm, quarter turn clockwise: centre at (0, 100),
        # so the robot ends at (100, 100).
        arc_length = 100.0 * math.pi / 2.0
        x, y, theta = arc_pose(0.0, 0.0, 0.0, arc_length, 90.0)
        self.assertAlmostEqual(x, 100.0, places=6)
        self.assertAlmostEqual(y, 100.0, places=6)
        self.assertAlmostEqual(theta, 90.0)

    def test_rejects_bad_geometry(self):
        with self.assertRaises(ValueError):
            wheel_circumference_mm(0.0)
        with self.assertRaises(ValueError):
            mm_per_motor_deg(56.0, 0.0)
        with self.assertRaises(ValueError):
            motor_deg_for_turn(90.0, 0.0, 56.0)


if __name__ == "__main__":
    unittest.main()
