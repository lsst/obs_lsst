# Configuration for auxTel
import os
from lsst.utils import getPackageDir

if hasattr(config, 'ccdKeys'):
    config.ccdKeys = ['detector', 'detectorName']

config.isr.load(os.path.join(getPackageDir("obs_lsstCam"), "config", "auxTel", "isr.py"))
