# Fiducial values derived from SMTN-002 (v2024-03-06), based on
# syseng_throughput v1.9. Gain values derived from ComCam PTC
# processed in u/jchiang/ptc_BLOCK-275_w_2024_28.
# See DM-45333 for more details.

# Note that we don’t have the real LSSTCam ones yet. As currently formulated,
# the fiducials depend on the detector gains, and it hasn't been decided yet
# how to "average" (or otherwise pick from) the detectors in LSSTCam.

# Fiducial ZeroPoint for 1s exposure
config.fiducialZeroPoint = {
    "u": 25.97,
    "g": 27.96,
    "r": 27.81,
    "i": 27.62,
    "z": 27.23,
    "y": 26.27,
}
