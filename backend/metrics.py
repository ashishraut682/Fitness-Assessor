import numpy as np
import math

def calculate_angle(a, b, c):
    """
    Calculates the 2D angle (in degrees) formed at vertex point `b` 
    between line segments (a -> b) and (b -> c).
    `a`, `b`, `c` are tuples or lists of (x, y).
    """
    a = np.array(a[:2])  # First joint (e.g. Hip)
    b = np.array(b[:2])  # Vertex joint (e.g. Knee)
    c = np.array(c[:2])  # Third joint (e.g. Ankle)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360.0 - angle

    return round(float(angle), 2)

def calculate_3d_angle(a, b, c):
    """
    Calculates the 3D angle (in degrees) formed at vertex point `b` using vectors ba and bc.
    `a`, `b`, `c` are tuples or lists of (x, y, z).
    """
    ba = np.array([a[0] - b[0], a[1] - b[1], a[2] - b[2]])
    bc = np.array([c[0] - b[0], c[1] - b[1], c[2] - b[2]])

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))

    return round(float(np.degrees(angle)), 2)

def calculate_body_stability(left_shoulder, right_shoulder, left_hip, right_hip):
    """
    Measures body symmetry and tilt stability (0 to 100).
    100 indicates perfect horizontal shoulder/hip alignment.
    """
    shoulder_tilt = abs(left_shoulder[1] - right_shoulder[1])
    hip_tilt = abs(left_hip[1] - right_hip[1])

    tilt_penalty = (shoulder_tilt + hip_tilt) * 200  # Scale factor for normalized coordinates
    stability_score = max(0.0, min(100.0, 100.0 - tilt_penalty))
    return round(stability_score, 2)

def calculate_arm_horizon(left_shoulder, left_wrist, right_shoulder, right_wrist):
    """
    Checks horizontal arm extension (for Yoga Warrior II or Basketball Defense).
    Returns horizontal alignment score (0 to 100).
    """
    left_diff = abs(left_shoulder[1] - left_wrist[1])
    right_diff = abs(right_shoulder[1] - right_wrist[1])

    penalty = (left_diff + right_diff) * 150
    return round(max(0.0, min(100.0, 100.0 - penalty)), 2)

def calculate_spine_lean(ear, hip, ankle):
    """
    Calculates torso/spine forward lean angle relative to vertical axis (for Athletics Sprint & Running).
    """
    dx = abs(ear[0] - hip[0])
    dy = abs(ear[1] - hip[1]) + 1e-6
    lean_angle = math.degrees(math.atan2(dx, dy))
    return round(float(lean_angle), 2)
