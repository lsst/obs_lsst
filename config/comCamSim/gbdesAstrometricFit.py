"""
comCamSim-specific overrides for GbdesAstrometricFitTask
"""
config.connections.referenceCatalog = "uw_stars_20240524"
config.applyRefCatProperMotion = False
config.referenceFilter = "lsst_r"
config.devicePolyOrder = 5
config.exposurePolyOrder = 7
