"""
lsstCam-specific overrides of CompareWarpAssembleCoaddTask
"""

# Load configs from base assembleCoadd
config.load("assembleCoadd.py")

# Preliminary aggressive adjustment to accomodate early commissioning
# deep-drilling-style cadence with many observations
# in rapid sucessions across only few nights.
config.maxFractionEpochsHigh = 0.2
config.prefilterArtifactsMaskPlanes.append("SPIKE")
config.prefilterArtifactsMaskPlanes.append("PARTLY_VIGNETTED")
