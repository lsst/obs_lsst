"""
LSST Cam-specific overrides for RunIsrTask
"""
import os.path

from lsst.utils import getPackageDir

obsConfigDir = os.path.join(getPackageDir("obs_lsst"), "config")

config.isr.load(os.path.join(obsConfigDir, "isr.py"))
