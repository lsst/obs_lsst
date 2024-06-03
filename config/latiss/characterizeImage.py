# Lower the detection threshold from its default of 5.0 for these short and often
# sparsely populated exposures. Along with the includeThresholdMultiplier = 10
# default, only sources with an effective threshold above 36 will make it into the
# catalog.
config.detection.thresholdValue = 3.6

# Some modifications to the objectSize selector for PSF estimation optimized
# for LATISS data.
config.measurePsf.starSelector["objectSize"].signalToNoiseMin = 10
config.measurePsf.starSelector["objectSize"].widthStdAllowed = 0.28
config.measurePsf.starSelector["objectSize"].widthMax = 14.0

# We are starved for PSF stars, so don't reserve any at this stage.
config.measurePsf.reserve.fraction = 0.0

# Reduce psfex spatialOrder to 1, this helps ensure success with low numbers of psf candidates.
config.measurePsf.psfDeterminer["psfex"].spatialOrder = 1
# Set the default kernel and stamp sizes for PSF modeling appropriate for LATISS
config.measurePsf.makePsfCandidates.kernelSize = 71
config.measurePsf.psfDeterminer["psfex"].stampSize = 71

config.installSimplePsf.width = 21
config.installSimplePsf.fwhm = 2.355*2  # LATISS plate scale is 2x LSST nominal

# Turn off S/N cut for aperture correction measurement source selection
# (it now only includes calib_psf_used objects, and that cut is "good
# enough" for the shallow LATISS data).
config.measureApCorr.sourceSelector["science"].doSignalToNoise = False

config.measurement.plugins["base_Jacobian"].pixelScale = 0.1

# Set the default aperture as appropriate for the LATISS plate scale.
config.measurement.algorithms["base_CompensatedTophatFlux"].apertures = [35]
config.normalizedCalibrationFlux.raw_calibflux_name = "base_CompensatedTophatFlux_35"
config.normalizedCalibrationFlux.measure_ap_corr.refFluxName = "base_CircularApertureFlux_35_0"
config.measurement.slots.apFlux = "base_CircularApertureFlux_35_0"
config.measurement.slots.calibFlux = "base_CircularApertureFlux_35_0"
