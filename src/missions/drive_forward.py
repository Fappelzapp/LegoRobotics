"""First drivetrain test: drive forward 100 mm (10 cm).

This is deliberately NOT the final drive base. It is a bounded, open-loop
check that answers two questions safely:

- do both drive motors run, and
- do their positive directions agree (so the robot goes straight, not spins)?

Why open loop and why a timeout:

- ``DriveBase.straight()`` waits for an average distance. If one motor is
  reversed relative to the other, the average can stay near zero and the call
  can keep driving. A direct ``run_angle`` plus a hard timeout cannot run away.
- No gyro heading correction is used, because we do not yet know which port is
  the left wheel. Turning the wrong way would fight the controller.

Ports and wheel diameter are the values reported by the team; the wheel
diameter is still UNMEASURED. The physical distance is therefore approximate.

Run:

    .venv/bin/pybricksdev run ble --name "LegoLabSpike1" src/missions/drive_forward.py
"""

import math

from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Stop
from pybricks.pupdevices import Motor
from pybricks.tools import StopWatch, wait

# --- parameters -----------------------------------------------------

LEFT_PORT = Port.A  # side assignment is a guess; straight motion is symmetric
RIGHT_PORT = Port.E

WHEEL_DIAMETER_MM = 56.0  # guessed — not measured
DISTANCE_MM = 100.0  # 10 cm
SPEED_DEG_S = 180  # ~88 mm/s at a 56 mm wheel
TIMEOUT_MS = 6000

# --------------------------------------------------------------------


def main():
    hub = PrimeHub()
    left = Motor(LEFT_PORT)
    right = Motor(RIGHT_PORT)

    motor_deg = DISTANCE_MM / (math.pi * WHEEL_DIAMETER_MM) * 360.0

    print(f"target_mm={DISTANCE_MM:.1f} target_motor_deg={motor_deg:.1f}")

    hub.imu.reset_heading(0)
    left.reset_angle(0)
    right.reset_angle(0)

    left.run_angle(SPEED_DEG_S, motor_deg, then=Stop.BRAKE, wait=False)
    right.run_angle(SPEED_DEG_S, motor_deg, then=Stop.BRAKE, wait=False)

    timer = StopWatch()
    while timer.time() < TIMEOUT_MS:
        if abs(left.angle() - motor_deg) < 5 and abs(right.angle() - motor_deg) < 5:
            break
        wait(20)

    left.brake()
    right.brake()
    wait(200)

    print(
        f"left_deg={left.angle():.1f} right_deg={right.angle():.1f} "
        f"heading_deg={hub.imu.heading():.1f}"
    )


if __name__ == "__main__":
    main()
