import os.path

OBS_CONFIG_DIR = os.path.dirname(__file__)

config.referenceCatalogLoader.refObjLoader.load(os.path.join(OBS_CONFIG_DIR, "filterMap.py"))
config.referenceCatalogLoader.doApplyColorTerms = False
config.connections.refCatalog =  "the_monster_20240904"

config.filterNames = ["SDSSg_65mm~empty",
                      "SDSSr_65mm~empty",
                      "SDSSi_65mm~empty",
                      "empty~SDSSi_65mm",
                      ]
