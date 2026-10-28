"""Team competition program, refactored from the user's 2026-10-28 paste.

Run this file on the hub; importing it on a laptop does NOT initialise hardware
or start missions. The laptop runner injects its own devices via configure().

IMPORTANT BEHAVIOUR CHANGES:
- motors_pid(stp, speed, amount) keeps amount in CENTIMETRES; speed is now
  conventional Pybricks mm/s (+forward), with no hidden sign flips.
- distance comes from DriveBase.distance(), using the source 62.4 mm diameter.
  Old 5.56 cm encoder calibration is NOT retained: routes need remeasurement.
- every motion helper brakes on exit, including timeout/exception.
- turn targets are absolute headings, resolved along the shortest path.

Unmeasured constants and proposed limits: lib/competition_config.py.
Preserved source transcription: docs/Attachments/PID-original-2026-10-28.py.txt.
Hub validation: not run. Verify motor polarity with wheels raised first.
"""

from math import pi

from lib import competition_config as config
from lib.competition_motion import Motion

hub = None
motors = None
modull = None
modulr = None
_motion = None
_wait = None


def configure(hub_device, drive_base, left_attachment, right_attachment,
              wait_function, stopwatch_factory):
    """Connect the same control/mission code to real OR simulated devices."""
    global hub, motors, modull, modulr, _motion, _wait
    hub, motors = hub_device, drive_base
    modull, modulr = left_attachment, right_attachment
    _wait = wait_function
    _motion = Motion(hub.imu, motors, wait_function, stopwatch_factory)


def setup_hardware():
    # Deliberately lazy: importing PID must never connect to or move a robot.
    from pybricks.hubs import PrimeHub
    from pybricks.parameters import Axis, Button, Color, Direction, Port
    from pybricks.pupdevices import Motor
    from pybricks.robotics import DriveBase
    from pybricks.tools import StopWatch, wait as hub_wait

    hub_device = PrimeHub(top_side=Axis.Z, front_side=Axis.Y)
    hub_device.light.on(Color.MAGENTA)
    hub_device.system.set_stop_button(Button.BLUETOOTH)
    left_direction = (Direction.COUNTERCLOCKWISE if config.GUESS_LEFT_FORWARD_IS_CCW
                      else Direction.CLOCKWISE)
    right_direction = (Direction.COUNTERCLOCKWISE if config.GUESS_RIGHT_FORWARD_IS_CCW
                       else Direction.CLOCKWISE)
    left = Motor(getattr(Port, config.LEFT_PORT), left_direction)
    right = Motor(getattr(Port, config.RIGHT_PORT), right_direction)
    left_attachment = Motor(getattr(Port, config.LEFT_MODULE_PORT), Direction.CLOCKWISE)
    right_attachment = Motor(getattr(Port, config.RIGHT_MODULE_PORT), Direction.CLOCKWISE)
    left_attachment.control.stall_tolerances(
        config.MODULE_STALL_SPEED_DPS, config.MODULE_STALL_TIME_MS,
    )
    drive = DriveBase(left, right, config.WHEEL_DIAMETER_MM, config.AXLE_TRACK_MM)
    # The custom outer loop owns gyro heading. DriveBase still controls wheel
    # speed internally; we are NOT trying to disable those motor-speed loops.
    drive.use_gyro(False)
    configure(hub_device, drive, left_attachment, right_attachment, hub_wait, StopWatch)
    timer = StopWatch()
    try:
        while not hub.imu.ready():
            if timer.time() >= config.IMU_READY_TIMEOUT_MS:
                raise RuntimeError("IMU not ready; place the robot flat and stationary")
            wait(config.LOOP_MS)
        hub.imu.reset_heading(0)
    except BaseException:
        stop_all()
        raise


def wait(time_ms):
    if _wait is None:
        raise RuntimeError("call setup_hardware() or configure() first")
    _wait(time_ms)


def motors_pid(stp, speed, amount):
    """Hold heading stp (deg); signed speed (mm/s); distance amount (cm)."""
    if _motion is None:
        raise RuntimeError("call setup_hardware() or configure() first")
    _motion.drive_heading(stp, speed, amount)


def ausrichten1(stp):
    """Gentler shortest-path turn to absolute heading stp (deg)."""
    _motion.align(stp, config.TURN_SLOW_KP)


def ausrichten2(stp):
    """Faster shortest-path turn to absolute heading stp (deg)."""
    _motion.align(stp, config.TURN_FAST_KP)


def motors_kurve1(target_angle, speed, steering):
    """Curve to absolute heading; steering is a TURN RATE in deg/s, not %."""
    _motion.curve(target_angle, speed, steering)


def timed_straight(motor_speed_dps, duration_ms):
    """Replace the two busy-loop raw-motor moves without changing their units.

    Their opposite raw motor signs imply straight travel, NOT an in-place spin.
    After normalising motor directions, one DriveBase command drives both sides.
    Conversion assumes the source direct drive (no unreported gearing).
    """
    speed_mm_s = motor_speed_dps * pi * config.WHEEL_DIAMETER_MM / 360.0
    try:
        motors.drive(speed_mm_s, 0)
        wait(duration_ms)
    finally:
        motors.brake()


def stop_all():
    if motors is not None:
        motors.brake()
    if modull is not None:
        modull.stop()
    if modulr is not None:
        modulr.stop()


# Mission call arguments and attachment concurrency are from the source paste.
# Explicit brake calls remain for readability even though helpers also brake.

def weg1():
    """Steine."""
    motors_pid(0, -400, 2)
    motors_pid(0, 500, 21)
    ausrichten2(-30)
    motors_pid(-30, 500, 30)
    ausrichten2(35)
    motors_pid(35, 500, 8)
    motors.brake()
    motors_kurve1(45, 100, 10)
    timed_straight(200, 1000)
    modulr.run_angle(500, 520)
    modull.run_angle(400, -200, wait=False)
    wait(1000)
    modulr.run_angle(500, -520)
    motors_pid(45, -200, 12)
    motors.brake()
    ausrichten2(27)
    motors_pid(27, -700, 2)
    ausrichten2(-25)
    motors_pid(-25, -900, 55)
    motors.brake()


def weg2():
    """Umarmung."""
    motors_pid(0, -400, 2)
    motors_pid(0, 400, 4)
    ausrichten2(-45)
    motors_pid(-45, 500, 30)
    motors_pid(-45, 300, 10)
    motors.brake()
    modulr.run_angle(600, 1000, wait=False)
    modull.run_angle(-600, 1100)
    wait(100)
    modulr.run_angle(600, -200, wait=False)
    modull.run_angle(800, 1100)
    modulr.stop()
    modull.stop()
    motors_pid(-45, -400, 15)
    ausrichten2(-65)
    motors_pid(-65, -900, 30)
    motors.brake()


def weg3(extra_module):
    """The shared route; LEFT adds the attachment sequence, RIGHT skips it."""
    motors_pid(0, -400, 2)
    motors_pid(0, 400, 37.5)
    motors.brake()
    for _ in range(4):
        modulr.run_angle(850, -150)
        wait(100)
        modulr.run_angle(850, 170)
        wait(100)
    ausrichten2(0)
    motors_pid(0, 400, 13.5)
    motors.brake()
    ausrichten2(-40)
    motors_pid(-40, 400, 14)
    ausrichten2(-90)
    motors_pid(-90, 400, 22)
    motors.brake()
    wait(500)
    ausrichten1(0)
    motors_pid(0, 150, 10)
    motors.brake()
    if extra_module:
        modull.run_angle(100, 600)
        motors_pid(0, -400, 15)
        motors.brake()
        modull.run_angle(200, -600, wait=False)
        wait(700)
        motors_pid(0, 200, 15)
        wait(300)
    else:
        wait(500)
    motors_pid(0, -500, 5)
    motors.brake()
    wait(200)
    ausrichten1(-90)
    motors_pid(-90, 700, 13)
    motors.brake()
    wait(200)
    ausrichten2(-150)
    motors_pid(-150, 700, 27.5)
    ausrichten2(-105)
    motors_pid(-105, 900, 60)
    motors.brake()


def weg4():
    """Schwinger."""
    motors_pid(0, -400, 27)
    modull.run_angle(-900, 450, wait=False)
    ausrichten2(35)
    motors_pid(35, -400, 21)
    ausrichten2(90)
    motors_pid(90, 400, 20)
    motors.brake()
    modulr.run_angle(400, 380)
    modull.run_angle(900, 600, wait=False)
    modulr.run_angle(400, -500)
    modull.run_angle(-900, 500)
    modulr.run_angle(400, -350, wait=False)
    motors_pid(90, -400, 14.5)
    ausrichten2(20)
    motors_pid(20, 800, 45)
    motors.brake()


def weg5():
    """Schwarz. The stall command requires a real mechanical end stop."""
    motors_pid(5, 400, 45)
    motors.brake()
    modull.run_until_stalled(-600, duty_limit=50)
    motors_pid(2, 500, 4)
    motors.brake()
    modulr.run_angle(-800, 900, wait=False)
    timed_straight(100, 1000)
    modull.run_angle(800, 860)
    motors_pid(5, -500, 55)
    motors.brake()


def weg6():
    """Lore zum anderen Team."""
    motors_pid(0, 400, 2)
    motors_pid(0, -600, 43)
    ausrichten2(90)
    motors_pid(90, -600, 23.5)
    ausrichten2(180)
    motors_pid(180, -600, 5.25)
    motors.brake()
    modulr.run_angle(400, -200)
    motors_pid(180, 300, 6)
    motors.brake()
    modulr.run_angle(200, 140)
    motors_pid(180, 250, 20)
    motors.brake()
    modull.run_angle(1200, -1000)
    wait(200)
    modull.run_angle(500, 400)
    modull.run_angle(1200, -400)
    wait(200)
    modull.run_angle(500, 800)
    motors_pid(180, -600, 3)
    modulr.run_angle(150, -200, wait=False)
    ausrichten2(90)
    motors.brake()
    motors_pid(90, 800, 15)
    ausrichten2(30)
    # Source says 30 above, but 20 here. Retained, NOT silently 'corrected'.
    motors_pid(20, 900, 40)
    motors.brake()


def weg7():
    """Sachen in Kreis."""
    motors_pid(0, -400, 2)
    motors_pid(0, 500, 29)
    ausrichten1(70)
    motors_pid(70, 200, 16)
    motors.brake()
    modull.run_angle(1000, 450, wait=False)
    modulr.run_angle(500, -350)
    motors_pid(70, 200, 5)
    motors.brake()
    modulr.run_angle(500, 250)
    motors_pid(70, -300, 25)
    motors.brake()
    ausrichten2(27)
    motors_pid(27, 500, 27)
    motors.brake()


def run_route(name):
    """Run one route without a button gate (also used by the laptop runner)."""
    if _motion is None:
        raise RuntimeError("call setup_hardware() or configure() first")
    routes = {"1": weg1, "2": weg2, "4": weg4, "5": weg5, "6": weg6, "7": weg7}
    if name not in routes and name not in ("3-left", "3-right"):
        raise ValueError("unknown route: " + str(name))
    motors.brake()
    hub.imu.reset_heading(0)
    hub.speaker.beep(100)
    try:
        if name in ("3-left", "3-right"):
            weg3(name == "3-left")
        else:
            routes[name]()
    except BaseException:
        stop_all()
        raise
    finally:
        motors.brake()


def _wait_for_press(button):
    # Require a fresh press, then release. No CPU-burning `pass` loops.
    while button in hub.buttons.pressed():
        wait(config.LOOP_MS)
    while button not in hub.buttons.pressed():
        wait(config.LOOP_MS)
    while button in hub.buttons.pressed():
        wait(config.LOOP_MS)


def _wait_for_route_start():
    from pybricks.parameters import Button
    motors.brake()
    _wait_for_press(Button.RIGHT)
    _wait_for_press(Button.LEFT)


def _select_variant():
    from pybricks.parameters import Button
    while Button.LEFT in hub.buttons.pressed() or Button.RIGHT in hub.buttons.pressed():
        wait(config.LOOP_MS)
    while True:
        pressed = hub.buttons.pressed()
        selected = Button.LEFT if Button.LEFT in pressed else Button.RIGHT if Button.RIGHT in pressed else None
        if selected is not None:
            while selected in hub.buttons.pressed():
                wait(config.LOOP_MS)
            _wait_for_press(selected)
            return "3-left" if selected == Button.LEFT else "3-right"
        wait(config.LOOP_MS)


def main():
    setup_hardware()
    try:
        for name in ("1", "2"):
            _wait_for_route_start()
            run_route(name)
        run_route(_select_variant())
        for name in ("4", "5", "6", "7"):
            _wait_for_route_start()
            run_route(name)
    finally:
        stop_all()


if __name__ == "__main__":
    main()
