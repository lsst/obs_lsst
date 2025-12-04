"""
lsstCam-specific overrides of CompareWarpAssembleCoaddTask
"""
import os.path

# Load configs from base assembleCoadd
config.load(os.path.join(os.path.dirname(__file__), "assembleCoadd.py"))

# Preliminary aggressive adjustment to accomodate early commissioning
# deep-drilling-style cadence with many observations
# in rapid sucessions across only few nights.
config.maxFractionEpochsHigh = 0.2
config.prefilterArtifactsMaskPlanes.append("SPIKE")
config.prefilterArtifactsMaskPlanes.append("PARTLY_VIGNETTED")
