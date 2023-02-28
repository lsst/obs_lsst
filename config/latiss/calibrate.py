from lsst.meas.astrom import FitAffineWcsTask

# Configure the photometry to use atlas_refcat2.
config.connections.photoRefCat = 'atlas_refcat2_20220201'
config.photoCal.match.referenceSelection.magLimit.fluxField = "r_flux"

# We often have very few sources due to smaller aperture so use affine task. 
config.astrometry.wcsFitter.retarget(FitAffineWcsTask)

# Note that the following two config values were validated on data taken in
# 2022-11 and 2022-12, which is after some major improvements were made to
# the pointing accuracy of AuxTel. The improvements came from updates made
# in 2022-05 (with further improvements throughout the year). As such, these
# configs are likely only appropriate for data starting from 2022-05. If
# processing earlier data, these may need to be relaxed to the previous values
# (pixelMargin = 900 & maxOffsetPix = 3000) to avoid astrometric fit failures.
config.astromRefObjLoader.pixelMargin = 250
config.astrometry.matcher.maxOffsetPix = 900

# These allow a better chance of finding a match for the otherwise "Unabel to
# match sources" cases.
config.astrometry.matcher.numPointsForShape = 5
config.astrometry.matcher.numPointsForShapeAttempt = 8

# Apply a magnitude limit and decrease the SNR limit as we're only a 1.2m
# and frequently take short exposures.
config.astrometry.referenceSelector.doMagLimit = True
config.astrometry.referenceSelector.magLimit.minimum = 8
config.astrometry.referenceSelector.magLimit.maximum = 18
config.astrometry.referenceSelector.magLimit.fluxField = "phot_g_mean_flux"
config.astrometry.matcher.maxRotationDeg = 2.0

config.astrometry.sourceFluxType = "Psf"
config.astrometry.sourceSelector['matcher'].sourceFluxType = "Psf"
config.astrometry.sourceSelector['matcher'].minSnr = 10

# Turn on reference vs. source magnitude outlier rejection to help avoid bad
# matches.
config.astrometry.doMagnitudeOutlierRejection = True

# Write srcMatchFull
config.doWriteMatchesDenormalized = True
