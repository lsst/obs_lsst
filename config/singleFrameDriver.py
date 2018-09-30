import os.path

from lsst.utils import getPackageDir

config.processCcd.load(os.path.join(getPackageDir("obs_lsst"), "config", "processCcd.py"))
config.ccdKey = 'detector'
