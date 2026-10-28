"""Stub of ``pybricks.tools``."""

import time as _time


def wait(ms):
    _time.sleep(ms / 1000.0)


class StopWatch:
    def __init__(self):
        self._start = _time.monotonic()

    def time(self):
        return int((_time.monotonic() - self._start) * 1000.0)

    def reset(self):
        self._start = _time.monotonic()
