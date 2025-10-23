"""LSSTComCam-specific overrides for detectCoaddSources"""

# The following detection adaptations have been proven to have potential
# to do more harm than is reasonable for any potential improvements.  The
# root causes leading to their addition (for HSC data) should be assessed
# and, if present, fixed instead.  Meantime, we do turn off the variance
# scaling and impose limits on the values the other two can take.
config.doScaleVariance = False
config.detection.minThresholdScaleFactor = 0.5
config.detection.maxThresholdScaleFactor = 1.2
config.detection.minBackgroundTweak = -8.0
config.detection.maxBackgroundTweak = 5.0
