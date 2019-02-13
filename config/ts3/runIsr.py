import os.path
from lsst.utils import getPackageDir

config.load(os.path.join(getPackageDir("obs_lsst"), "config", "ts3", "ts3.py"))
