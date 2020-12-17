import os
from lsst.utils import getPackageDir

config.functorFile = os.path.join(getPackageDir('obs_lsst'), 'policy', 'imsim', 'Source.yaml')
