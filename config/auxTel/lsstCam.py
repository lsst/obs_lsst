import os.path
from lsst.utils import getPackageDir

config.load(os.path.join(getPackageDir("obs_lsstCam"), "config", "auxTel", "auxTel.py"))
