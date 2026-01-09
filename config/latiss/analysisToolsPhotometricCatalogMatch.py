config.referenceCatalogLoader.refObjLoader.load("filterMap.py")
config.referenceCatalogLoader.doApplyColorTerms = True
config.referenceCatalogLoader.colorterms.load("colorterms.py")

config.connections.refCatalog = "atlas_refcat2_20220201"
config.filterNames = ["SDSSg_65mm~empty",
                      "SDSSr_65mm~empty",
                      "SDSSi_65mm~empty",
                      "empty~SDSSi_65mm",
                      ]
