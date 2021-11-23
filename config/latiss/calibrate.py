import os
from lsst.utils import getPackageDir
from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask
from lsst.obs.lsst.filters import LATISS_FILTER_DEFINITIONS

REFCAT_NAME = 'gaia'
# REFCAT_NAME = 'ps1'

if REFCAT_NAME == 'gaia':
    REFCAT = "gaia_dr2_20200414"
    config.doPhotoCal = False
else:
    REFCAT = "ps1_pv3_3pi_20170110"


# Reference catalog
# config.calibrate.refObjLoader.retarget(LoadIndexedReferenceObjectsTask)
# config.calibrate.refObjLoader.load(os.path.join(getPackageDir("obs_lsst"), "config", "filterMap.py"))

# config.calibrate.refObjLoader.ref_dataset_name="cal_ref_cat"
config.connections.astromRefCat = REFCAT
config.connections.photoRefCat = REFCAT

for refObjLoader in (
                     config.astromRefObjLoader,
                     config.photoRefObjLoader):
    refObjLoader.retarget(LoadIndexedReferenceObjectsTask)
    refObjLoader.ref_dataset_name = REFCAT

filtMap = {}
filts = LATISS_FILTER_DEFINITIONS
if REFCAT_NAME == 'gaia':
    for filt in filts._filters:
        filtMap[filt.band] = 'phot_g_mean'

else:  # Pan-STARRS:
    # TODO: add a mag limit here - it's super slow without it
    for filt in filts._filters:
        if len(filt.band) == 1:  # skip 'white' etc
            filtMap[filt.band] = filt.band


config.astromRefObjLoader.filterMap = filtMap
config.photoRefObjLoader.filterMap = filtMap

config.doDeblend = False

###########


config.photoCal.match.referenceSelection.magLimit.fluxField = "i_flux"

if "ext_shapeHSM_HsmShapeRegauss" in config.measurement.plugins:
    # no deblending has been done
    config.measurement.plugins["ext_shapeHSM_HsmShapeRegauss"].deblendNChild = ""
