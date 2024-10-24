"""Overrides for PhotometricCatalogMatchTask"""

import os.path

configDir = os.path.dirname(__file__)
config.referenceCatalogLoader.refObjLoader.load(os.path.join(configDir, "filterMap.py"))
config.referenceCatalogLoader.doApplyColorTerms = False
