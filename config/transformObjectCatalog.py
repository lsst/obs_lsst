import os
from lsst.utils import getPackageDir

config.load(os.path.join(getPackageDir("obs_lsst"), "config", "filterMap.py"))
config.functorFile = os.path.join(getPackageDir("obs_lsst"), 'policy', 'Object.yaml')
