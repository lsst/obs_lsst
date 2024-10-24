import os.path

OBS_CONFIG_DIR = os.path.dirname(__file__)

config.referenceCatalogLoader.refObjLoader.load(os.path.join(OBS_CONFIG_DIR, "filterMap.py"))
config.referenceCatalogLoader.doApplyColorTerms = True
config.referenceCatalogLoader.colorterms.load(os.path.join(OBS_CONFIG_DIR, "colorterms.py"))

config.connections.refCatalog = "atlas_refcat2_20220201"
