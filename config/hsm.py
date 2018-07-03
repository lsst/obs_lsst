import os.path
from lsst.utils import getPackageDir
config.load(os.path.join(getPackageDir("meas_extensions_shapeHSM"), "config", "enable.py"))
config.plugins["ext_shapeHSM_HsmShapeRegauss"].deblendNChild = "deblend_nChild"
