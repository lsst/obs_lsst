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
config.select.maxStarEPerBand = {
    "u": 0.2,
    "g": 0.2,
    "r": 0.2,
    "i": 0.2,
    "z": 0.2,
    "y": 0.2,
    "fallback": 0.2,
}
config.select.maxStarUnNormalizedEPerBand = {
    "u": 2.3,
    "g": 2.3,
    "r": 2.3,
    "i": 2.3,
    "z": 2.3,
    "y": 2.3,
    "fallback": 2.3,
}

config.select.excludeDetectors = [0, 20, 27, 65, 123, 161, 168, 188]
