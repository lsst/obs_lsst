import os
from lsst.utils import getPackageDir

# Always produce these output bands in the Object Tables,
# regardless which bands were processed
config.outputBands = ["u", "g", "r", "i", "z", "y"]

config.functorFile = os.path.join(getPackageDir('obs_lsst'), 'policy', 'imsim', 'Object.yaml')
