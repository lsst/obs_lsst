import os.path

from lsst.meas.algorithms import ColorLimit

config_dir = os.path.dirname(__file__)

# Some modifications to the objectSize selector for PSF estimation optimized
# for LATISS data.
config.psf_measure_psf.starSelector["objectSize"].signalToNoiseMin = 10
config.psf_measure_psf.starSelector["objectSize"].widthStdAllowed = 0.28
config.psf_measure_psf.starSelector["objectSize"].widthMax = 14.0

# We are starved for PSF stars, so don't reserve any at this stage.
config.psf_measure_psf.reserve.fraction = 0.0

# Reduce psfex spatialOrder to 1, this helps ensure success with low numbers
# of psf candidates.
config.psf_measure_psf.psfDeterminer["psfex"].spatialOrder = 1
# Set the default kernel and stamp sizes for PSF modeling for LATISS.7
config.psf_measure_psf.makePsfCandidates.kernelSize = 71
config.psf_measure_psf.psfDeterminer["psfex"].stampSize = 71
config.psf_measure_psf.psfDeterminer["psfex"].photometricFluxField = \
    "base_CircularApertureFlux_35_0_instFlux"

config.psf_source_measurement.plugins["base_CircularApertureFlux"].radii = [35.0]
config.psf_source_measurement.plugins["base_CompensatedTophatFlux"].apertures = [35]
config.psf_source_measurement.slots.apFlux = "base_CircularApertureFlux_35_0"
config.psf_source_measurement.slots.calibFlux = "base_CircularApertureFlux_35_0"

config.install_simple_psf.width = 21
config.install_simple_psf.fwhm = 2.355 * 2  # LATISS plate scale is 2x LSST nominal

# Turn off S/N cut for aperture correction measurement source selection
# (it now only includes calib_psf_used objects, and that cut is "good
# enough" for the shallow LATISS data).
config.psf_normalized_calibration_flux.raw_calibflux_name = "base_CompensatedTophatFlux_35"
config.psf_normalized_calibration_flux.measure_ap_corr.refFluxName = "base_CircularApertureFlux_35_0"
config.psf_normalized_calibration_flux.measure_ap_corr.sourceSelector["science"].doSignalToNoise = False
# Put in the correct override fields in case we revisit this in the future.
config.psf_normalized_calibration_flux.measure_ap_corr.sourceSelector["science"].signalToNoise.fluxField = \
    "base_CompensatedTophatFlux_35_instFlux"
config.psf_normalized_calibration_flux.measure_ap_corr.sourceSelector["science"].signalToNoise.errField = \
    "base_CompensatedTophatFlux_35_instFluxErr"

config.measure_aperture_correction.sourceSelector["science"].doSignalToNoise = False

# Configure the photometry to use atlas_refcat2.
config.connections.photometry_ref_cat = "atlas_refcat2_20220201"
config.photometry_ref_loader.load(os.path.join(config_dir, "filterMap.py"))

config.photometry.match.referenceSelection.magLimit.fluxField = "r_flux"
colors = config.photometry.match.referenceSelection.colorLimits
colors["g-r"] = ColorLimit(primary="g_flux", secondary="r_flux", minimum=0.4, maximum=2.0)

config.photometry.applyColorTerms = True
config.photometry.photoCatName = "atlas_refcat2_20220201"
config.photometry.colorterms.load(os.path.join(config_dir, "colorterms.py"))

# Note that the following two config values were validated on data taken in
# 2022-11 and 2022-12, which is after some major improvements were made to
# the pointing accuracy of AuxTel. The improvements came from updates made
# in 2022-05 (with further improvements throughout the year). As such, these
# configs are likely only appropriate for data starting from 2022-05. If
# processing earlier data, these may need to be relaxed to the previous values
# (pixelMargin = 900 & maxOffsetPix = 3000) to avoid astrometric fit failures.
config.astrometry_ref_loader.pixelMargin = 250
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

# Set the default aperture as appropriate for the LATISS plate scale.
config.star_measurement.plugins["base_CircularApertureFlux"].radii = [35.0]
config.star_measurement.plugins["base_CompensatedTophatFlux"].apertures = [35]
config.star_measurement.slots.apFlux = "base_CircularApertureFlux_35_0"
config.star_measurement.slots.calibFlux = "base_CircularApertureFlux_35_0"
config.star_normalized_calibration_flux.raw_calibflux_name = "base_CompensatedTophatFlux_35"
