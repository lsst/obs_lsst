import os
from lsst.utils import getPackageDir
from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask, MagnitudeLimit
from lsst.obs.lsst.filters import LATISS_FILTER_DEFINITIONS
from lsst.meas.astrom import FitAffineWcsTask

REFCAT_NAME = 'gaia'
# REFCAT_NAME = 'ps1'

if REFCAT_NAME == 'gaia':
    REFCAT = "gaia_dr2_20200414"
    config.doPhotoCal = False
else:
    REFCAT = "ps1_pv3_3pi_20170110"

config.connections.astromRefCat = REFCAT
config.connections.photoRefCat = REFCAT

for refObjLoader in (config.astromRefObjLoader,
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
if "ext_shapeHSM_HsmShapeRegauss" in config.measurement.plugins:
    # no deblending has been done
    config.measurement.plugins["ext_shapeHSM_HsmShapeRegauss"].deblendNChild = ""

config.photoCal.match.referenceSelection.magLimit.fluxField = "i_flux"

####### new today
config.astrometry.wcsFitter.retarget(FitAffineWcsTask)

# should these ever differ, or should we tie them together like this?
MAXOFFSET = 3000
config.astromRefObjLoader.pixelMargin = 1000
config.astrometry.matcher.maxOffsetPix = MAXOFFSET

magLimit = MagnitudeLimit()
magLimit.minimum = 1
magLimit.maximum = 18
config.astrometry.referenceSelector.doMagLimit = True
config.astrometry.referenceSelector.magLimit = magLimit
config.astrometry.referenceSelector.magLimit.fluxField = "phot_g_mean_flux"
config.astrometry.matcher.maxRotationDeg = 5.99
config.astrometry.sourceSelector['matcher'].minSnr = 10
