import lsst.fgcmcal as fgcmcal

physical_to_band = {
    "u_02": "u",
    "g_01": "g",
    "r_03": "r",
    "i_06": "i",
    "z_03": "z",
    "y_04": "y",
}

config.outfileBase = "fgcmLSSTComCam"
# Our first runs will use just g/r/i.
config.bands = ["g", "r", "i"]
config.fitBands = ["g", "r", "i"]
config.physicalFilterMap = physical_to_band
config.requiredBands = ["g", "r", "i"]

config.cycleNumber = 0
config.maxIterBeforeFinalCycle = 50
config.minCcdPerExp = 1
config.utBoundary = 0.0
config.washMjds = (0.0,)
# For now, define 1 observing epoch that encompasses everything.
config.epochMjds = (0.0, 100000.0)
config.coatingMjds = []
config.latitude = -30.2333
config.mirrorArea = 34.524
config.cameraGain = 1.0
config.defaultCameraOrientation = 0.0
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
# Fit aperture corrections with only 2 bins to exercise the code.
config.aperCorrFitNBins = 10
config.aperCorrInputSlopeDict = {"g": 0.0,
                                 "r": 0.0,
                                 "i": 0.0}

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
    "g": fgcmcal.Sedterm(primaryTerm="gr", secondaryTerm="ri", constant=1.5),
    "r": fgcmcal.Sedterm(primaryTerm="gr", secondaryTerm="ri", constant=0.9),
    "i": fgcmcal.Sedterm(primaryTerm="ri", secondaryTerm="gr", constant=0.5,
                         extrapolated=True, primaryBand="i", secondaryBand="r", tertiaryBand="g"),
}

config.starColorCuts = ("g, i, 0.50, 3.5",)
config.refStarColorCuts = ("g, i, 0.5, 3.5",)
# Use a tiny fraction of reference stars to test true self-calibration.
config.refStarMaxFracUse = 0.001
config.useExposureReferenceOffset = False
config.precomputeSuperStarInitialCycle = False
config.superStarSubCcdDict = {
    "u": True,
    "g": True,
    "r": True,
    "i": True,
    "z": True,
}
# Allow calibration to work with at least 10 exposures per night.
config.minExpPerNight = 10
# Allow calibration to work with very few stars per exposure.
config.minStarPerExp = 100
config.nStarPerRun = 5000
config.nExpPerRun = 100
config.colorSplitBands = ["g", "i"]
config.freezeStdAtmosphere = True
# For tests, do low-order per-ccd polynomial.
config.superStarSubCcdChebyshevOrder = 2
config.ccdGraySubCcdDict = {
    "u": False,
    "g": True,
    "r": True,
    "i": True,
    "z": True,
    "y": True,
}
config.ccdGrayFocalPlaneDict = {
    "u": True,
    "g": True,
    "r": True,
    "i": True,
    "z": True,
    "y": True,
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
config.sigFgcmMaxEGrayDict = {
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

config.deltaAperFitPerCcdNx = 4
config.deltaAperFitPerCcdNy = 4
config.doComputeDeltaAperPerVisit = False
config.doComputeDeltaAperMap = True
config.doComputeDeltaAperPerCcd = True
config.deltaAperInnerRadiusArcsec = 2.40
config.deltaAperOuterRadiusArcsec = 3.40
