import os
from lsst.utils import getPackageDir
from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask, MagnitudeLimit
from lsst.obs.lsst.filters import LATISS_FILTER_DEFINITIONS
from lsst.meas.astrom import FitAffineWcsTask

ASTROM_REFCAT_NAME = 'gaia_dr2_20200414'
PHOTO_REFCAT_NAME = 'ps1_pv3_3pi_20170110'

config.connections.astromRefCat = ASTROM_REFCAT_NAME
config.astromRefObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.astromRefObjLoader.ref_dataset_name = ASTROM_REFCAT_NAME
config.astromRefObjLoader.anyFilterMapsToThis = 'phot_g_mean'
config.astromRefObjLoader.filterMap = {}  # TODO: remove after DM-33270

config.connections.photoRefCat = PHOTO_REFCAT_NAME
config.photoRefObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.photoRefObjLoader.ref_dataset_name = PHOTO_REFCAT_NAME

psFiltMap = {}
filts = LATISS_FILTER_DEFINITIONS
for filt in filts._filters:
    if len(filt.band) == 1:  # skip 'white' etc
        psFiltMap[filt.band] = filt.band

config.photoRefObjLoader.filterMap = psFiltMap

config.doDeblend = False
if "ext_shapeHSM_HsmShapeRegauss" in config.measurement.plugins:
    # no deblending has been done
    config.measurement.plugins["ext_shapeHSM_HsmShapeRegauss"].deblendNChild = ""

config.photoCal.match.referenceSelection.magLimit.fluxField = "i_flux"


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
