"""comCamSim-specific overrides for PhotometricCatalogMatchTask"""

import os.path

configDir = os.path.dirname(__file__)
config.referenceCatalogLoader.refObjLoader.load(os.path.join(configDir, "filterMap.py"))
config.referenceCatalogLoader.doApplyColorTerms = False

config.connections.refCatalog = "uw_stars_20240524"
config.filterNames = ("g", "r", "i")
