import unittest

from tests import _path  # noqa: F401
from lib.grid import Grid


class GridTests(unittest.TestCase):
    def test_world_to_cell_round_trip(self):
        grid = Grid(25.0, 20, 20)
        self.assertEqual(grid.world_to_cell(0.0, 0.0), (0, 0))
        self.assertEqual(grid.world_to_cell(25.0, 50.0), (1, 2))
        x, y = grid.cell_to_world(1, 2)
        self.assertAlmostEqual(x, 25.0)
        self.assertAlmostEqual(y, 50.0)

    def test_straight_path(self):
        grid = Grid(10.0, 10, 10)
        path = grid.plan((0.0, 0.0), (50.0, 0.0))
        self.assertIsNotNone(path)
        self.assertEqual(path[0], (0.0, 0.0))
        self.assertEqual(path[-1], (50.0, 0.0))
        self.assertEqual(len(path), 6)

    def test_wall_forces_detour(self):
        # Vertical wall at i = 2 for j = 0..8; the only gap is at j = 9.
        blocked = {(2, j) for j in range(9)}
        grid = Grid(10.0, 10, 10, blocked)
        path = grid.plan((0.0, 50.0), (40.0, 50.0))
        self.assertIsNotNone(path)
        self.assertTrue(any(y == 90.0 for _, y in path))
        self.assertGreater(len(path), 5)

    def test_unreachable_returns_none(self):
        blocked = {(2, j) for j in range(10)}
        grid = Grid(10.0, 10, 10, blocked)
        self.assertIsNone(grid.plan((0.0, 50.0), (40.0, 50.0)))

    def test_blocked_start_returns_none(self):
        grid = Grid(10.0, 5, 5, blocked_cells={(0, 0)})
        self.assertIsNone(grid.plan((0.0, 0.0), (40.0, 40.0)))

    def test_no_corner_cutting(self):
        # Block both orthogonal neighbours of the diagonal from (1,1) to (2,2).
        blocked = {(2, 1), (1, 2)}
        grid = Grid(10.0, 5, 5, blocked)
        path = grid.plan((10.0, 10.0), (20.0, 20.0))
        self.assertIsNotNone(path)
        self.assertGreater(len(path), 2)

    def test_rejects_bad_grid(self):
        with self.assertRaises(ValueError):
            Grid(0.0, 5, 5)
        with self.assertRaises(ValueError):
            Grid(10.0, 0, 5)


if __name__ == "__main__":
    unittest.main()
