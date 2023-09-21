config.connections.cycleNumber = 6

from lsst.obs.lsst.filters import LATISS_FILTER_DEFINITIONS
config.physicalFilterMap = LATISS_FILTER_DEFINITIONS.physical_to_band
