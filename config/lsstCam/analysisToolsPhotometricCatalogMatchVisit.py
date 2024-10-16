"""Overrides for PhotometricCatalogMatchTask"""

import os.path

configDir = os.path.dirname(__file__)
config.referenceCatalogLoader.refObjLoader.load(os.path.join(configDir, "filterMap.py"))

config.connections.refCatalog = "atlas_refcat2_20220201"
config.referenceCatalogLoader.doApplyColorTerms = False
