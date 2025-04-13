"""LSSTCam-specific overrides for MakePsfMatchedWarpTask"""

# Keep in sync with the makeWarp.py config.
# TODO: DM-50110
config.modelPsf.defaultFwhm = 11.0
