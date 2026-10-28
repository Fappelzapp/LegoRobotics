import unittest

from tests import _path  # noqa: F401  (side effect: sys.path)
from lib.pid import PID


class PIDTests(unittest.TestCase):
    def test_proportional_only(self):
        pid = PID(kp=2.0)
        self.assertAlmostEqual(pid.update(10.0, 0.0, 0.1), 20.0)

    def test_output_limit(self):
        pid = PID(kp=2.0, output_limit=15.0)
        self.assertAlmostEqual(pid.update(10.0, 0.0, 0.1), 15.0)

    def test_integral_accumulates_and_clamps(self):
        pid = PID(kp=0.0, ki=1.0, i_limit=5.0)
        pid.update(10.0, 0.0, 0.1)  # integral = 1
        self.assertAlmostEqual(pid.update(10.0, 0.0, 0.1), 2.0)
        for _ in range(100):
            output = pid.update(10.0, 0.0, 0.1)
        self.assertAlmostEqual(output, 5.0)

    def test_derivative_on_measurement_has_no_target_kick(self):
        pid = PID(kp=1.0, kd=1.0)
        pid.update(0.0, 0.0, 0.1)  # prime the derivative history
        # Target steps 0 -> 10 while measurement is unchanged: derivative is 0.
        self.assertAlmostEqual(pid.update(10.0, 0.0, 0.1), 10.0)

    def test_derivative_opposes_measurement_motion(self):
        pid = PID(kp=0.0, kd=1.0)
        pid.update(0.0, 0.0, 0.1)
        # Measurement rises by 1 in 0.1 s: derivative = 10, output = -10.
        self.assertAlmostEqual(pid.update(0.0, 1.0, 0.1), -10.0)

    def test_deadband_treats_small_error_as_zero(self):
        pid = PID(kp=1.0, deadband=0.5)
        self.assertAlmostEqual(pid.update(0.4, 0.0, 0.1), 0.0)
        self.assertAlmostEqual(pid.update(1.0, 0.0, 0.1), 1.0)

    def test_non_positive_dt_returns_zero(self):
        pid = PID(kp=1.0)
        self.assertEqual(pid.update(10.0, 0.0, 0.0), 0.0)
        self.assertEqual(pid.update(10.0, 0.0, -1.0), 0.0)

    def test_reset_clears_integral(self):
        pid = PID(kp=0.0, ki=1.0)
        pid.update(10.0, 0.0, 0.1)
        pid.reset()
        self.assertAlmostEqual(pid.update(10.0, 0.0, 0.1), 1.0)

    def test_rejects_bad_limits(self):
        with self.assertRaises(ValueError):
            PID(kp=1.0, output_limit=0.0)
        with self.assertRaises(ValueError):
            PID(kp=1.0, i_limit=-1.0)
        with self.assertRaises(ValueError):
            PID(kp=1.0, deadband=-0.1)


if __name__ == "__main__":
    unittest.main()
