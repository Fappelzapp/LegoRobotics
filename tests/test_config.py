import unittest

from tests import _path  # noqa: F401
from lib import config


class ConfigTests(unittest.TestCase):
    def test_geometry_is_positive(self):
        self.assertGreater(config.WHEEL_DIAMETER_MM, 0)
        self.assertGreater(config.AXLE_TRACK_MM, 0)
        self.assertGreater(config.GEAR_RATIO, 0)

    def test_required_ports_are_set(self):
        for name in (
            "PORT_LEFT_MOTOR",
            "PORT_RIGHT_MOTOR",
            "PORT_COLOUR_LEFT",
            "PORT_COLOUR_RIGHT",
            "PORT_DISTANCE",
        ):
            self.assertTrue(hasattr(config, name), name)


if __name__ == "__main__":
    unittest.main()
