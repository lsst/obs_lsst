"""LSST-specific overrides for MeasureMergedCoaddSourcesTask"""

import os.path
from lsst.utils import getPackageDir
from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask

config.measurement.load(os.path.join(getPackageDir("obs_lsst"), "config", "apertures.py"))
config.measurement.load(os.path.join(getPackageDir("obs_lsst"), "config", "kron.py"))
config.measurement.load(os.path.join(getPackageDir("obs_lsst"), "config", "convolvedFluxes.py"))
config.measurement.load(os.path.join(getPackageDir("obs_lsst"), "config", "hsm.py"))
config.load(os.path.join(getPackageDir("obs_lsst"), "config", "cmodel.py"))

config.match.refObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.match.refObjLoader.ref_dataset_name = "cal_ref_cat"
config.match.refObjLoader.load(os.path.join(getPackageDir("obs_lsst"), "config", "filterMap.py"))

config.doWriteMatchesDenormalized = True

#
# This isn't good!  There appears to be no way to configure the base_PixelFlags measurement
# algorithm based on a configuration parameter; see DM-4159 for a discussion.  The name
# BRIGHT_MASK must match assembleCoaddConfig.brightObjectMaskName
#
config.measurement.plugins["base_PixelFlags"].masksFpCenter.append("BRIGHT_OBJECT")
config.measurement.plugins["base_PixelFlags"].masksFpAnywhere.append("BRIGHT_OBJECT")

config.measurement.plugins.names |= ["base_InputCount"]
