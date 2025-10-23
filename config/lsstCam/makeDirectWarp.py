"""LSSTCam-specific overrides for MakeDirectWarpTask"""

# These thresholds have been conditioned on the latest DRP run (DM-48371)
# which used the w_2025_02 pipeline and the LSSTComCam/DP1-RC1/defaults
# collection.
config.select.maxPsfTraceRadiusDelta = 4.4
config.select.maxPsfApFluxDelta = 1.6

# Correspond to more loose values chosen early in ComCam commissioning
config.select.maxEllipResidual = 0.19
config.select.maxScaledSizeScatter = 0.07
config.select.maxPsfApCorrSigmaScaledDelta = 0.15

config.select.excludeDetectors = [0, 20, 27, 65, 123, 161, 168, 188]
