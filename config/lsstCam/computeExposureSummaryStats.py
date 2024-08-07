import os.path

config_dir = os.path.dirname(__file__)

# Fiducial values derived from SMTN-002 (v2024-03-06), based on
# syseng_throughput v1.9. Gain values derived from ComCam PTC
# processed in u/jchiang/ptc_BLOCK-275_w_2024_28.
# See DM-45333 for more details.

# Fiducial PsfSigma in pixels
config.fiducialPsfSigma = {
    "u": 1.72,
    "g": 1.63,
    "r": 1.56,
    "i": 1.51,
    "z": 1.47,
    "y": 1.44,
}

# Fiducial ZeroPoint for 1s exposure
config.fiducialZeroPoint = {
    'u': 25.97,
    'g': 27.96,
    'r': 27.81,
    'i': 27.62,
    'z': 27.23,
    'y': 26.27,
}

# Fiducial SkyBackground in ADU per second
config.fiducialSkyBackground = {
    'u': 0.91,
    'g': 9.35,
    'r': 19.94,
    'i': 32.04,
    'z': 48.05,
    'y': 54.81,
}
