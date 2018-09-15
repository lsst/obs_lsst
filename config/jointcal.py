import os.path
from lsst.utils import getPackageDir

if hasattr(config.astrometryRefObjLoader, "ref_dataset_name"):
    config.astrometryRefObjLoader.ref_dataset_name = 'cal_ref_cat'
if hasattr(config.photometryRefObjLoader, "ref_dataset_name"):
    config.photometryRefObjLoader.ref_dataset_name = 'cal_ref_cat'

filterMapFile = os.path.join(getPackageDir('obs_lsstCam'), 'config', 'filterMap.py')
config.astrometryRefObjLoader.load(filterMapFile)
config.photometryRefObjLoader.load(filterMapFile)
