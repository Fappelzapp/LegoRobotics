"""Single source of truth for tunable numbers.

Every value carries a provenance tag:

- ``measured``  — taken from the physical robot, method recorded
- ``datasheet`` — from LEGO or PyBricks documentation
- ``guessed``   — a placeholder that must be replaced before a real run

The values below are placeholders. Do not treat them as this robot's geometry.
See docs/Guides/Agent Quickstart.md for the measurement procedure.
"""

from pybricks.parameters import Port

# --- Drive geometry -------------------------------------------------

WHEEL_DIAMETER_MM = 56.0  # guessed — common large-wheel nominal, NOT measured
AXLE_TRACK_MM = 112.0  # guessed — placeholder, NOT measured
GEAR_RATIO = 1.0  # guessed — motor revolutions per wheel revolution

# Motor polarity: set True for a side whose positive direction is backwards.
LEFT_MOTOR_INVERTED = False  # guessed
RIGHT_MOTOR_INVERTED = False  # guessed

# --- Ports ----------------------------------------------------------

PORT_LEFT_MOTOR = Port.A  # team reported drive motors on A and E; side is a guess
PORT_RIGHT_MOTOR = Port.E  # team reported drive motors on A and E; side is a guess
PORT_COLOUR_LEFT = Port.C  # guessed
PORT_COLOUR_RIGHT = Port.D  # guessed
PORT_DISTANCE = Port.E  # guessed

# --- PID starting points --------------------------------------------
# Guessed. Tune on the hub; see docs/Reference/PID Tuning.md.

DISTANCE_KP = 1.0
DISTANCE_KI = 0.0
DISTANCE_KD = 0.0
DISTANCE_OUTPUT_LIMIT = 100.0  # % motor power
DISTANCE_DEADBAND_MM = 2.0

HEADING_KP = 1.0
HEADING_KI = 0.0
HEADING_KD = 0.0
HEADING_OUTPUT_LIMIT = 60.0  # % differential power
HEADING_DEADBAND_DEG = 0.5

# --- Motion limits --------------------------------------------------

STRAIGHT_SPEED_MMS = 200  # guessed
TURN_RATE_DPS = 120  # guessed
POSITION_TOLERANCE_MM = 20  # proposal
HEADING_TOLERANCE_DEG = 3.0  # proposal
