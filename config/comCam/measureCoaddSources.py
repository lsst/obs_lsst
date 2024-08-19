"""comCam-specific overrides for MeasureMergedCoaddSourcesTask"""

import os.path

config.match.refObjLoader.load(os.path.join(os.path.dirname(__file__), "filterMap.py"))
config.connections.refCat = "atlas_refcat2_20220201"
