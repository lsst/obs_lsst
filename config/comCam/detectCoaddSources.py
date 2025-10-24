"""LSSTComCam-specific overrides for detectCoaddSources"""

# The following detection adaptations have been proven to have potential
# to do more harm than is reasonable for any potential improvements.  The
# root causes leading to their addition (for HSC data) should be assessed
# and, if present, fixed instead.
config.doScaleVariance = False
config.detection.doBackgroundTweak = False
config.detection.doThresholdScaling = False
