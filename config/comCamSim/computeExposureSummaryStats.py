import os.path

config_dir = os.path.dirname(__file__)

# Fiducial values derived from SMTN-002 (v2024-03-06), based on syseng_throughput v1.9.
# See SMTN-002 (https://smtn-002.lsst.io) and DM-44855 for discussion.

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
    "u": 25.96,
    "g": 27.95,
    "r": 27.80,
    "i": 27.61,
    "z": 27.22,
    "y": 26.26,
}

# Fiducial SkyBackground in ADU per second
config.fiducialSkyBackground = {
    "u": 0.90,
    "g": 9.20,
    "r": 19.62,
    "i": 31.51,
    "z": 47.26,
    "y": 53.91,
}
