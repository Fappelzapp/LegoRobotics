"""Settings for PID.py, separate from the unrelated scaffold in config.py.

Source = the user's 2026-10-28 competition-program paste, NOT a measurement.
GUESS/proposal values must be checked on the robot. No gains are hub-tuned here.
This module has no Pybricks imports, so the laptop uses exactly the same settings.
"""

WHEEL_DIAMETER_MM = 62.4  # source constant; actual rolling diameter unmeasured
AXLE_TRACK_MM = 106.0  # source constant; centre-to-centre measurement unverified
LEFT_PORT = "E"  # source: links
RIGHT_PORT = "A"  # source: rechts
LEFT_MODULE_PORT = "F"  # source: modull
RIGHT_MODULE_PORT = "B"  # source: modulr

# Inference from the original timed straight moves: links.run(-v), rechts.run(v).
# Confirm with wheels raised BEFORE running a mission. Not a hardware observation.
GUESS_LEFT_FORWARD_IS_CCW = True
GUESS_RIGHT_FORWARD_IS_CCW = False

LOOP_MS = 20  # user-requested wait; real dt includes work done between waits
HEADING_KP = 4.0  # source gain, now outputs body turn rate in deg/s
HEADING_KI = 0.0  # source: disabled
# Source kd=1 multiplied a per-pass difference. At a nominal 20 ms, 1*0.020
# gives equivalent continuous-time scaling (seconds). Derived, NOT retuned.
HEADING_KD = 1.0 * LOOP_MS / 1000.0
INTEGRAL_LIMIT_DEG_S = 30.0  # proposal: bounds accumulated error, not motor power
MAX_TURN_RATE_DPS = 180.0  # proposal: safety cap; not a measured motor limit

ACCELERATION_MM_S2 = 600.0  # proposal: replaces the iteration-count speed ramp
DECELERATION_MM_S2 = 600.0  # proposal: stopping-distance envelope, not a guarantee
MIN_DRIVE_SPEED_MM_S = 50.0  # source curve floor, proposed for straight moves too
DISTANCE_TOLERANCE_MM = 1.0  # proposal: encoder-distance completion tolerance
TURN_TOLERANCE_DEG = 2.0  # proposal: replaces exact integer equality
TURN_SETTLE_MS = 100  # proposal: require several in-tolerance readings
CURVE_TOLERANCE_DEG = 3.0  # source: motors_kurve1
CURVE_SLOWDOWN_DEG = 10.0  # source: last 10 degrees

# Source turn gains (motor deg/s per heading degree) converted to BODY deg/s
# under the inferred direct-drive geometry. These are NOT the same unit as kp.
MOTOR_TO_BODY_TURN = WHEEL_DIAMETER_MM / AXLE_TRACK_MM
TURN_SLOW_KP = 3.0 * MOTOR_TO_BODY_TURN  # derived from ausrichten1
TURN_FAST_KP = 5.0 * MOTOR_TO_BODY_TURN  # derived from ausrichten2
MIN_TURN_RATE_DPS = 30.0 * MOTOR_TO_BODY_TURN  # source +/-30 motor-deg/s kick
TURN_TIMEOUT_MS = 10000  # proposal: fail rather than spin indefinitely
MOVE_TIMEOUT_MARGIN_MS = 3000  # proposal: allowances for acceleration / lag
MOVE_TIMEOUT_FACTOR = 4.0  # proposal: multiple of nominal travel time
IMU_READY_TIMEOUT_MS = 10000  # proposal: calibrate stationary before a mission

MODULE_STALL_SPEED_DPS = 300  # source: modull.control.stall_tolerances
MODULE_STALL_TIME_MS = 50  # source
