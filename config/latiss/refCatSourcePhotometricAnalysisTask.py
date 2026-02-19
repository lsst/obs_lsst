from lsst.pipe.tasks.postprocess import TransformObjectCatalogConfig

# By default loop over all the same bands that are present in the Object Table
objectConfig = TransformObjectCatalogConfig()
objectConfig.load("transformObjectCatalog.py")
config.bands = objectConfig.outputBands

config.connections.refCatalog = "atlas_refcat2_20220201"
config.connections.outputName = "sourceTable_visit_atlas_refcat2_20220201_match_photom"
