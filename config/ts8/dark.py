import os.path
from lsst.utils import getPackageDir

config.load(os.path.join(getPackageDir("obs_lsst"), "config", "ts8", "ts8.py"))

config.repair.cosmicray.nCrPixelMax = 1000000
