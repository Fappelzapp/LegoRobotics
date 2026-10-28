"""Field grid and A* path planner.

Pure Python. Cells are integer indices; world coordinates are millimetres.

Conventions match the rest of the library: +X forward, +Y right, heading
positive clockwise.

This module is a proposal: it has unit tests but has not been driven on a robot.
"""

import heapq
import math

_SQRT2 = math.sqrt(2.0)

# (dx, dy, cost)
_NEIGHBOURS = (
    (1, 0, 1.0),
    (-1, 0, 1.0),
    (0, 1, 1.0),
    (0, -1, 1.0),
    (1, 1, _SQRT2),
    (1, -1, _SQRT2),
    (-1, 1, _SQRT2),
    (-1, -1, _SQRT2),
)


class Grid:
    def __init__(
        self,
        resolution_mm,
        width_cells,
        height_cells,
        blocked_cells=(),
        origin_mm=(0.0, 0.0),
    ):
        if resolution_mm <= 0:
            raise ValueError("resolution_mm must be positive")
        if width_cells <= 0 or height_cells <= 0:
            raise ValueError("grid dimensions must be positive")

        self.resolution_mm = float(resolution_mm)
        self.width_cells = int(width_cells)
        self.height_cells = int(height_cells)
        self.origin_mm = (float(origin_mm[0]), float(origin_mm[1]))
        self.blocked = {(int(i), int(j)) for i, j in blocked_cells}

    # -- coordinates ---------------------------------------------------

    def world_to_cell(self, x_mm, y_mm):
        i = int(round((x_mm - self.origin_mm[0]) / self.resolution_mm))
        j = int(round((y_mm - self.origin_mm[1]) / self.resolution_mm))
        return i, j

    def cell_to_world(self, i, j):
        return (
            self.origin_mm[0] + i * self.resolution_mm,
            self.origin_mm[1] + j * self.resolution_mm,
        )

    def in_bounds(self, i, j):
        return 0 <= i < self.width_cells and 0 <= j < self.height_cells

    def is_free(self, i, j):
        return self.in_bounds(i, j) and (i, j) not in self.blocked

    # -- planning ------------------------------------------------------

    def plan(self, start_xy, goal_xy):
        """Return cell-centre waypoints from start to goal, or ``None``.

        Uses A* with 8-connectivity, an admissible Euclidean heuristic, and a
        no-corner-cutting rule. The returned list includes both ends.
        """
        start = self.world_to_cell(*start_xy)
        goal = self.world_to_cell(*goal_xy)

        if not self.is_free(*start) or not self.is_free(*goal):
            return None

        if start == goal:
            return [self.cell_to_world(*start)]

        def heuristic(i, j):
            return math.hypot(goal[0] - i, goal[1] - j)

        open_heap = [(heuristic(*start), 0.0, start[0], start[1])]
        came_from = {}
        g_score = {start: 0.0}
        closed = set()

        while open_heap:
            _, g, i, j = heapq.heappop(open_heap)
            node = (i, j)

            if node in closed:
                continue
            if node == goal:
                return self._reconstruct(came_from, node)
            closed.add(node)

            for dx, dy, step_cost in _NEIGHBOURS:
                ni, nj = i + dx, j + dy
                if not self.is_free(ni, nj):
                    continue

                # A diagonal move may not squeeze between two blocked cells.
                if dx != 0 and dy != 0:
                    if not self.is_free(i + dx, j) or not self.is_free(i, j + dy):
                        continue

                neighbour = (ni, nj)
                if neighbour in closed:
                    continue

                tentative = g + step_cost
                if tentative < g_score.get(neighbour, math.inf):
                    g_score[neighbour] = tentative
                    came_from[neighbour] = node
                    f = tentative + heuristic(ni, nj)
                    heapq.heappush(open_heap, (f, tentative, ni, nj))

        return None

    def _reconstruct(self, came_from, node):
        cells = [node]
        while node in came_from:
            node = came_from[node]
            cells.append(node)
        cells.reverse()
        return [self.cell_to_world(i, j) for i, j in cells]
