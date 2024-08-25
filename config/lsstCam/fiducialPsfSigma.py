# Fiducial values derived from SMTN-002 (v2024-03-06), based on
# syseng_throughput v1.9. Gain values derived from ComCam PTC
# processed in u/jchiang/ptc_BLOCK-275_w_2024_28.
# See DM-45333 for more details.

# Note that we don’t have the real LSSTCam ones yet. As currently formulated,
# the fiducials depend on the detector gains, and it hasn't been decided yet
# how to "average" (or otherwise pick from) the detectors in LSSTCam.

# Fiducial PsfSigma in pixels
config.fiducialPsfSigma = {
    "u": 1.72,
    "g": 1.63,
    "r": 1.56,
    "i": 1.51,
    "z": 1.47,
    "y": 1.44,
}
