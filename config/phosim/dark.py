import os.path
from lsst.utils import getPackageDir

config.load(os.path.join(getPackageDir("obs_lsst"), "config", "lsstCam.py"))

# avoids dark product building failure
config.repair.cosmicray.nCrPixelMax = 100000000
