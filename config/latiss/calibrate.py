from lsst.meas.algorithms import ColorLimit
from lsst.meas.astrom import FitAffineWcsTask

config.photoCal.match.referenceSelection.magLimit.fluxField = "r_flux"
colors = config.photoCal.match.referenceSelection.colorLimits
colors["g-r"] = ColorLimit(primary="g_flux", secondary="r_flux", minimum=0.4, maximum=2.0)
config.photoCal.applyColorTerms = True
config.photoCal.photoCatName = "atlas_refcat2_20220201"
config.connections.photoRefCat = "atlas_refcat2_20220201"
config.photoCal.colorterms.load("colorterms.py")

# Configure the photometry to use atlas_refcat2.
config.photoRefObjLoader.load("filterMap.py")

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
config.astrometry.sourceSelector["matcher"].sourceFluxType = "Psf"
config.astrometry.sourceSelector["matcher"].minSnr = 10

config.measurement.plugins["base_Jacobian"].pixelScale = 0.1

# Set the default aperture as appropriate for the LATISS plate scale.
config.measurement.algorithms["base_CompensatedTophatFlux"].apertures = [35]
config.normalizedCalibrationFlux.raw_calibflux_name = "base_CompensatedTophatFlux_35"

config.measurement.slots.apFlux = "base_CircularApertureFlux_35_0"
config.measurement.slots.calibFlux = "base_CircularApertureFlux_35_0"
