import os.path
from lsst.utils import getPackageDir

config.load(os.path.join(getPackageDir("obs_lsstCam"), "config", "lsstCam.py"))

# Cosmic rays
config.charImage.repair.cosmicray.nCrPixelMax = 1000000
config.charImage.repair.cosmicray.cond3_fac2 = 0.4
