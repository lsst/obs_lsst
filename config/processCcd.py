import os.path
from lsst.utils import getPackageDir
from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask

config.load(os.path.join(getPackageDir("obs_lsstCam"), "config", "lsstCam.py"))

# Cosmic rays
config.charImage.repair.cosmicray.nCrPixelMax = 1000000
config.charImage.repair.cosmicray.cond3_fac2 = 0.4

# Reference catalog
for refObjLoader in (config.charImage.refObjLoader,
                     config.calibrate.astromRefObjLoader,
                     config.calibrate.photoRefObjLoader):
    refObjLoader.retarget(LoadIndexedReferenceObjectsTask)
    refObjLoader.load(os.path.join(getPackageDir('obs_lsstCam'), 'config', 'filterMap.py'))
