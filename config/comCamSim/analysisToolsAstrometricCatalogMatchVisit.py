"""comCamSim-specific overrides for AstrometricCatalogMatchVisitTask"""

# refCatalog is the connections' defaultTemplate which controls connections
# prerequisite input refCat and output matchedCatalog
config.referenceCatalogLoader.refObjLoader.anyFilterMapsToThis = "lsst_g"
config.connections.refCatalog = "uw_stars_20240524"
config.referenceCatalogLoader.refObjLoader.requireProperMotion = False
