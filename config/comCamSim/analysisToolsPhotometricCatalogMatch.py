"""comCamSim-specific overrides for PhotometricCatalogMatchTask"""

import os.path
configDir = os.path.dirname(__file__)
config.referenceCatalogLoader.refObjLoader.load(os.path.join(configDir, 'filterMap.py'))
config.referenceCatalogLoader.doApplyColorTerms = False

config.connections.refCatalog = "uw_stars_20240228"
config.connections.matchedCatalog = "objectTable_tract_uw_stars_20240228_photoMatch"
config.filterNames = ("g", "r", "i")
