"""Pure drive-base geometry.

No ``pybricks`` import: safe to run in ``tests/`` on a laptop.

Conventions follow PyBricks:
- distances in millimetres,
- angles in degrees,
- heading and turn angle positive clockwise,
- ``+Y`` is to the robot's right.
"""

import math


def wheel_circumference_mm(diameter_mm):
    if diameter_mm <= 0:
        raise ValueError("diameter_mm must be positive")
    return math.pi * diameter_mm


def mm_per_motor_deg(diameter_mm, gear_ratio=1.0):
    """Millimetres of ground travel per degree of motor rotation.

    ``gear_ratio`` is motor revolutions per wheel revolution.
    """
    if gear_ratio <= 0:
        raise ValueError("gear_ratio must be positive")
    return wheel_circumference_mm(diameter_mm) / (360.0 * gear_ratio)


def motor_deg_for_mm(distance_mm, diameter_mm, gear_ratio=1.0):
    return distance_mm / mm_per_motor_deg(diameter_mm, gear_ratio)


def motor_deg_for_turn(angle_deg, axle_track_mm, diameter_mm, gear_ratio=1.0):
    """Motor degrees each wheel must travel for an in-place turn.

    The result is signed with the turn angle. For a positive (clockwise) turn
    the left wheel travels ``+result`` and the right wheel ``-result``.
    """
    if axle_track_mm <= 0:
        raise ValueError("axle_track_mm must be positive")
    wheel_deg = angle_deg * axle_track_mm / diameter_mm
    return wheel_deg / gear_ratio


def wrap_deg(angle_deg):
    """Normalise an angle to ``(-180, 180]``."""
    wrapped = angle_deg % 360.0
    if wrapped > 180.0:
        wrapped -= 360.0
    return wrapped


def arc_pose(x_mm, y_mm, theta_deg, d_mm, dtheta_deg):
    """Return the new pose after moving ``d_mm`` along an arc.

    ``d_mm`` is the travel of the robot centre; ``dtheta_deg`` is the heading
    change, positive clockwise. Uses the exact arc solution when the heading
    change is non-zero.
    """
    theta = math.radians(theta_deg)
    dtheta = math.radians(dtheta_deg)

    if abs(dtheta) < 1e-12:
        new_x = x_mm + d_mm * math.cos(theta)
        new_y = y_mm + d_mm * math.sin(theta)
    else:
        radius = d_mm / dtheta
        new_x = x_mm + radius * (math.sin(theta + dtheta) - math.sin(theta))
        new_y = y_mm - radius * (math.cos(theta + dtheta) - math.cos(theta))

    return new_x, new_y, wrap_deg(theta_deg + dtheta_deg)
