import lsst.fgcmcal as fgcmcal


physical_to_band = {
    "u_24": "u",
    "g_6": "g",
    "r_57": "r",
    "i_39": "i",
    "z_20": "z",
    "y_10": "y",
}

config.outfileBase = "fgcmLSSTCam"
config.bands = ["u", "g", "r", "i", "z", "y"]
config.fitBands = ["u", "g", "r", "i", "z", "y"]
config.physicalFilterMap = physical_to_band
config.requiredBands = []

config.doMultipleCycles = True
config.multipleCyclesFinalCycleNumber = 5

config.cycleNumber = 0
config.maxIterBeforeFinalCycle = 100
config.minCcdPerExp = 10
config.utBoundary = 0.0
config.washMjds = (0.0,)
# We have an observing epoch split at 2025-07-03 (new sequencer).
# Another epoch split at 2025-10-01 (during Sept/Oct shutdown).
config.epochMjds = (0.0, 60859.0, 60949.0, 100000.0)
config.coatingMjds = []
config.latitude = -30.2333
config.mirrorArea = 34.524
config.cameraGain = 1.0
config.defaultCameraOrientation = 0.0
config.expFwhmCutDict = {
    "u": 2.0,
    "g": 2.0,
    "r": 2.0,
    "i": 2.0,
    "z": 2.0,
    "y": 2.0,
}
config.expGrayPhotometricCutDict = {
    "u": -0.10,
    "g": -0.05,
    "r": -0.05,
    "i": -0.05,
    "z": -0.05,
    "y": -0.05,
}
config.expGrayHighCutDict = {
    "u": 0.2,
    "g": 0.2,
    "r": 0.2,
    "i": 0.2,
    "z": 0.2,
    "y": 0.2,
}
config.expVarGrayPhotometricCutDict = {
    "u": 0.15,
    "g": 0.05,
    "r": 0.05,
    "i": 0.05,
    "z": 0.05,
    "y": 0.05,
}
config.autoPhotometricCutNSig = 3.0
config.autoHighCutNSig = 3.0
config.aperCorrUsePsfFwhm = True
config.aperCorrPerCcd = False
config.aperCorrFitNBins = 10
config.aperCorrInputSlopeDict = {"u": 0.0,
                                 "g": 0.0,
                                 "r": 0.0,
                                 "i": 0.0,
                                 "z": 0.0,
                                 "y": 0.0}

config.sedboundaryterms = fgcmcal.SedboundarytermDict()
config.sedboundaryterms.data["ug"] = fgcmcal.Sedboundaryterm(primary="u",
                                                             secondary="g")
config.sedboundaryterms.data["gr"] = fgcmcal.Sedboundaryterm(primary="g",
                                                             secondary="r")
config.sedboundaryterms.data["ri"] = fgcmcal.Sedboundaryterm(primary="r",
                                                             secondary="i")
config.sedboundaryterms.data["iz"] = fgcmcal.Sedboundaryterm(primary="i",
                                                             secondary="z")
config.sedboundaryterms.data["zy"] = fgcmcal.Sedboundaryterm(primary="z",
                                                             secondary="y")

config.sedterms = fgcmcal.SedtermDict()
config.sedterms.data = {
    "u": fgcmcal.Sedterm(primaryTerm="ug", secondaryTerm="gr", constant=0.5,
                         extrapolated=True, primaryBand="u", secondaryBand="g", tertiaryBand="r"),
    "g": fgcmcal.Sedterm(primaryTerm="gr", secondaryTerm="ri", constant=1.5),
    "r": fgcmcal.Sedterm(primaryTerm="gr", secondaryTerm="ri", constant=0.9),
    "i": fgcmcal.Sedterm(primaryTerm="ri", secondaryTerm="iz", constant=1.1),
    "z": fgcmcal.Sedterm(primaryTerm="iz", secondaryTerm="ri", constant=1.0,
                         extrapolated=True, primaryBand="z", secondaryBand="i", tertiaryBand="r"),
    "y": fgcmcal.Sedterm(primaryTerm="zy", secondaryTerm="iz", constant=1.0,
                         extrapolated=True, primaryBand="y",
                         secondaryBand="z", tertiaryBand="i"),
}

config.starColorCuts = ("g, i, 0.0, 3.5",)
config.refStarColorCuts = ("g, i, 0.4, 1.0",)
# Use a large fraction of reference stars until we get image quality
# under control
config.refStarMaxFracUse = 0.5
config.useExposureReferenceOffset = False
# TODO DM-50133: This should not be necessary after illumination corrections.
config.precomputeSuperStarInitialCycle = True
config.superStarSubCcdDict = {
    "u": True,
    "g": True,
    "r": True,
    "i": True,
    "z": True,
    "y": True,
}
config.ccdGrayFocalPlaneMaxStars = 10000
# Allow calibration to work with at least 3 exposures per night.
config.minExpPerNight = 3
config.minStarPerExp = 500
config.nExpPerRun = 100
config.colorSplitBands = ["g", "i"]
config.freezeStdAtmosphere = True
config.superStarSubCcdChebyshevOrder = 2
config.ccdGraySubCcdDict = {
    "u": True,
    "g": True,
    "r": True,
    "i": True,
    "z": True,
    "y": True,
}
config.ccdGrayFocalPlaneDict = {
    "u": False,
    "g": False,
    "r": False,
    "i": False,
    "z": False,
    "y": False,
}
config.ccdGrayFocalPlaneFitMinCcd = 3
config.ccdGrayFocalPlaneChebyshevOrder = 2
config.modelMagErrors = True
# Do not fit instrumental parameters (mirror decay) per band.
config.instrumentParsPerBand = False
# Set the random seed for repeatability in fits.
config.randomSeed = 12345
# Do not use star repeatability metrics for selecting exposures.
# (Instead, use exposure repeatability metrics).
config.useRepeatabilityForExpGrayCutsDict = {
    "u": False,
    "g": False,
    "r": False,
    "i": False,
    "z": False,
    "y": False,
}
config.sigFgcmMaxErr = 0.005
config.sigFgcmMaxEGrayDict = {
    # We let the u-band be a little bit worse than the
    # other bands.
    "u": 0.15,
    "g": 0.05,
    "r": 0.05,
    "i": 0.05,
    "z": 0.05,
    "y": 0.05,
}
config.approxThroughputDict = {
    "u": 1.0,
    "g": 1.0,
    "r": 1.0,
    "i": 1.0,
    "z": 1.0,
    "y": 1.0,
}

config.deltaAperFitPerCcdNx = 8
config.deltaAperFitPerCcdNy = 8
config.doComputeDeltaAperPerVisit = False
config.doComputeDeltaAperMap = True
config.deltaAperFitSpatialNside = 32
config.doComputeDeltaAperPerCcd = True
config.deltaAperInnerRadiusArcsec = 2.40
config.deltaAperOuterRadiusArcsec = 3.40
