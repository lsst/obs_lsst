import os.path

OBS_CONFIG_DIR = os.path.dirname(__file__)

config.referenceCatalogLoader.refObjLoader.load(os.path.join(OBS_CONFIG_DIR, "filterMap.py"))
