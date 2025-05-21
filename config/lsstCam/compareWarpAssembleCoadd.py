"""
lsstCam-specific overrides of CompareWarpAssembleCoaddTask
"""

config.subregionSize = (10000, 100)
config.assembleStaticSkyModel.subregionSize = (10000, 100)
# Preliminary aggressive adjustment to accomodate early commissioning
# deep-drilling-style cadence with many observations
# in rapid sucessions across only few nights.
config.maxFractionEpochsHigh = 0.2
