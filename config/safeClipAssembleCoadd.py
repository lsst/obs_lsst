import os.path
from lsst.utils import getPackageDir

# Load configs from base assembleCoadd
config.load(os.path.join(getPackageDir("obs_lsst"), "config", "assembleCoadd.py"))
