import os.path
from lsst.utils import getPackageDir

config.bgModel.load(os.path.join(getPackageDir('obs_lsst'), 'config',
                                 'focalPlaneBackground.py'))
