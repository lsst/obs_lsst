import os
from lsst.utils import getPackageDir
from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask, MagnitudeLimit
from lsst.obs.lsst.filters import LATISS_FILTER_DEFINITIONS
from lsst.meas.astrom import FitAffineWcsTask

# support independent refcats for astrometry and photometry
ASTROM_REFCAT_NAME = 'gaia_dr2_20200414' # TODO: remove after DM-27013 once Gaia DR2 is default

# configure the astrometry, TODO: remove after DM-27013 once Gaia DR2 is default
config.connections.astromRefCat = ASTROM_REFCAT_NAME
config.astromRefObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.astromRefObjLoader.ref_dataset_name = ASTROM_REFCAT_NAME
config.astromRefObjLoader.anyFilterMapsToThis = 'phot_g_mean'
config.astromRefObjLoader.filterMap = {} 

# Configure the photometry to use atlas_refcat2. 
PHOTO_REFCAT_NAME = 'atlas_refcat2_20220201'
config.connections.photoRefCat = PHOTO_REFCAT_NAME
config.photoRefObjLoader.ref_dataset_name = PHOTO_REFCAT_NAME

# Configure the filter map for atlas refcat2. 
atlasFilterMap = {}
filts = LATISS_FILTER_DEFINITIONS
for filt in filts._filters:
    if len(filt.band) == 1:  # skip 'white' etc
        atlasFilterMap[filt.band] = filt.band
config.photoRefObjLoader.filterMap = atlasFilterMap
config.photoCal.match.referenceSelection.magLimit.fluxField = "r_flux"

# Turn on deblending
config.doDeblend = True
if "ext_shapeHSM_HsmShapeRegauss" in config.measurement.plugins:
    # if no deblending has been done this is required to not crash
    config.measurement.plugins["ext_shapeHSM_HsmShapeRegauss"].deblendNChild = ""

# We often have very few sources due to smaller aperture so use affine task. 
config.astrometry.wcsFitter.retarget(FitAffineWcsTask)

# Increase maxoffset as AUXTEL pointing can be unreliable, pixelMargin also increased to 
# ensure refcat overlap when we see large pointing offsets. 
MAXOFFSET = 3000
config.astromRefObjLoader.pixelMargin = 1000
config.astrometry.matcher.maxOffsetPix = MAXOFFSET

# Apply a magnitude limit and decrease the SNR limit as we're only a 1.2m
# and frequently take short exposures. Also, allow max rotation while the
# instrumental repeatability isn't good.
magLimit = MagnitudeLimit()
magLimit.minimum = 1
magLimit.maximum = 18
config.astrometry.referenceSelector.doMagLimit = True
config.astrometry.referenceSelector.magLimit = magLimit
config.astrometry.referenceSelector.magLimit.fluxField = "phot_g_mean_flux"
config.astrometry.matcher.maxRotationDeg = 5.99
config.astrometry.sourceSelector['matcher'].minSnr = 10

# Write srcMatchFull
config.doWriteMatchesDenormalized = True
