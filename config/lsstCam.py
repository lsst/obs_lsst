# Configuration for lsstCam
import os
from lsst.utils import getPackageDir

if hasattr(config, 'ccdKeys'):
    config.ccdKeys = ['detector', 'snap', 'raftName', 'detectorName']

if hasattr(config, 'doCameraImage'):
    config.doCameraImage = False

config.isr.load(os.path.join(getPackageDir("obs_lsstCam"), "config", "isr.py"))
