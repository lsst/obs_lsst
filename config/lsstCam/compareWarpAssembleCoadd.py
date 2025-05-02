"""
LSSTCam-specific overrides of CompareWarpAssembleCoaddTask
"""

config.subregionSize = (10000, 100)
config.assembleStaticSkyModel.subregionSize = (10000, 100)

# Preliminary aggressive adjustment to accomodate early commissioning cadence
# increase the threshold for transient vs static designation from 3% to 20%
config.maxFractionEpochsHigh=0.2

# Shrink regions protected from clipping conservatively
# This config protects the PSFs
config.detectTemplate.nSigmaToGrow=1.2
config.detectTemplate.thresholdValue=100
