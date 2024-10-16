import os.path
from lsst.pipe.tasks.postprocess import TransformObjectCatalogConfig

# By default loop over all the same bands that are present in the Object Table
objectConfig = TransformObjectCatalogConfig()
objectConfig.load(os.path.join(os.path.dirname(__file__), "transformObjectCatalog.py"))
config.bands = objectConfig.outputBands
config.connections.refCatalog =  "the_monster_20240904"
config.connections.outputName = "objectTable_tract_the_monster_20240904_match_photom"