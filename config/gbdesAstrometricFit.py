"""
Rubin-instrument specific overrides for GbdesAstrometricFitTask
"""
config.devicePolyOrder = 5
config.exposurePolyOrder = 7
config.fitProperMotion = True
config.useColor = True
# The reference color was chosen by looking at the median g-i color in the
# catalog of standard stars produced by fgcmFitCycle.
config.referenceColor = 1.439
config.connections.colorCatalog = "fgcm_Cycle5_StandardStars"
