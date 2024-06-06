"""comCamSim-specific overrides for MeasureMergedCoaddSourcesTask"""

import os.path

config.match.refObjLoader.load(os.path.join(os.path.dirname(__file__), "filterMap.py"))
config.connections.refCat = "uw_stars_20240524"
