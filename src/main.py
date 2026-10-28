"""Hub entry point.

Placeholder until the team's drive base code arrives. It proves the toolchain
and the display/speaker path, nothing about driving.

Run on the hub from the ``src/`` project root, for example:

    pybricksdev run ble main.py

This file imports the real ``pybricks`` package, so it will not run on a bare
laptop unless ``src/sim`` is on ``sys.path``.
"""

from pybricks.hubs import PrimeHub
from pybricks.parameters import Color
from pybricks.tools import wait


def main():
    hub = PrimeHub()
    hub.display.text("Hi")
    hub.light.on(Color.GREEN)
    hub.speaker.beep(frequency=600, duration=150)
    print("LegoRobotics scaffold: hello from the hub")
    wait(1000)


if __name__ == "__main__":
    main()
