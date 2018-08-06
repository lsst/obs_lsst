import os.path
from lsst.utils import getPackageDir

# Load configs from base assembleCoadd
config.load(os.path.join(getPackageDir("obs_lsstCam"), "config", "assembleCoadd.py"))

# 200 rows (since patch width is typically < 10k pixels
config.assembleStaticSkyModel.subregionSize = (10000, 200)

# FUTURE Set to True if we run meas_mosaic or jointcal
config.assembleStaticSkyModel.doApplyUberCal = False
