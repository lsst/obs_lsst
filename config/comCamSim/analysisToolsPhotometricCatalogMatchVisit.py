"""comCamSim-specific overrides for PhotometricCatalogMatchVisitTask"""

import os.path
configDir = os.path.dirname(__file__)
config.referenceCatalogLoader.refObjLoader.load(os.path.join(configDir, 'filterMap.py'))

config.connections.refCatalog = "uw_stars_20240524"
config.referenceCatalogLoader.doApplyColorTerms = False
