"""comCamSim-specific overrides for AstrometricCatalogMatchTask"""

config.bands = ("g", "r", "i")
config.referenceCatalogLoader.refObjLoader.anyFilterMapsToThis = "lsst_g"
# refCatalog is the connections' defaultTemplate which controls connections
# prerequisite input refCat and output matchedCatalog
config.connections.refCatalog = "uw_stars_20240524"
config.referenceCatalogLoader.refObjLoader.requireProperMotion = False
