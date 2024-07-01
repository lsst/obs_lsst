import lsst.fgcmcal as fgcmcal

physical_to_band = {
    "g_01": "g",
    "r_03": "r",
    "i_06": "i",
}

config.outfileBase = "fgcmComCamSimCalibrations"
# The comcamsim survey uses g, r, i bands.
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
config.defaultCameraOrientation = 0.0
config.expGrayPhotometricCutDict = {"g": -0.05, "r": -0.05, "i": -0.05}
config.expGrayHighCutDict = {"g": 0.2, "r": 0.2, "i": 0.2}
config.expVarGrayPhotometricCutDict = {"g": 0.1**2.,
                                       "r": 0.1**2.,
                                       "i": 0.1**2.}
config.autoPhotometricCutNSig = 3.0
config.autoHighCutNSig = 3.0
# Fit aperture corrections with only 2 bins to exercise the code.
config.aperCorrFitNBins = 10
config.aperCorrInputSlopeDict = {"g": 0.0,
                                 "r": 0.0,
                                 "i": 0.0}

config.sedboundaryterms = fgcmcal.SedboundarytermDict()
config.sedboundaryterms.data["gr"] = fgcmcal.Sedboundaryterm(primary="g",
                                                             secondary="r")
config.sedboundaryterms.data["ri"] = fgcmcal.Sedboundaryterm(primary="r",
                                                             secondary="i")

config.sedterms = fgcmcal.SedtermDict()
config.sedterms.data = {
    "g": fgcmcal.Sedterm(primaryTerm="gr", secondaryTerm="ri", constant=1.5),
    "r": fgcmcal.Sedterm(primaryTerm="gr", secondaryTerm="ri", constant=0.9),
    "i": fgcmcal.Sedterm(primaryTerm="ri", secondaryTerm="gr", constant=0.5,
                         extrapolated=True, primaryBand="i", secondaryBand="r", tertiaryBand="g"),
}

# Define good stars with an r-i color cut.
config.starColorCuts = ("g, i, 0.50, 3.5",)
config.refStarColorCuts = ("g, i, 0.5, 1.5",)
# Use a tiny fraction of reference stars to test true self-calibration.
config.refStarMaxFracUse = 0.001
config.useExposureReferenceOffset = False
config.precomputeSuperStarInitialCycle = False
config.superStarSubCcdDict = {"g": True,
                              "r": True,
                              "i": True}
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
config.ccdGraySubCcdDict = {"g": True,
                            "r": True,
                            "i": True}
config.ccdGrayFocalPlaneDict = {"g": True,
                                "r": True,
                                "i": True}
config.ccdGrayFocalPlaneFitMinCcd = 3
config.ccdGrayFocalPlaneChebyshevOrder = 2
config.modelMagErrors = True
# Fix the sigma_cal calibration noise to 0.003 mag.
config.sigmaCalRange = (0.003, 0.003)
# Do not fit instrumental parameters (mirror decay) per band.
config.instrumentParsPerBand = False
# Set the random seed for repeatability in fits.
config.randomSeed = 12345
# Do not use star repeatability metrics for selecting exposures.
# (Instead, use exposure repeatability metrics).
config.useRepeatabilityForExpGrayCutsDict = {"g": False,
                                             "r": False,
                                             "i": False}
config.sigFgcmMaxEGrayDict = {"g": 0.05,
                              "r": 0.05,
                              "i": 0.05}
config.approxThroughputDict = {"g": 1.0,
                               "r": 1.0,
                               "i": 1.0}

config.deltaAperFitPerCcdNx = 16
config.deltaAperFitPerCcdNy = 16
config.doComputeDeltaAperPerVisit = False
config.doComputeDeltaAperMap = True
config.doComputeDeltaAperPerCcd = True
config.deltaAperInnerRadiusArcsec = 2.40
config.deltaAperOuterRadiusArcsec = 3.40
