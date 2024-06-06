import lsst.fgcmcal as fgcmcal

# We use our own filter to band mapping to limit to only the
# filters used in the photometric survey which may be input
# to fgcmcal. This override will be less important after
# TODO: DM-44705.
physical_to_band = {
    "SDSSg_65mm~empty": "g",
    "SDSSr_65mm~empty": "r",
    "SDSSi_65mm~empty": "i",
    "empty~SDSSi_65mm": "i",
    "SDSSz_65mm~empty": "z",
    "SDSSy_65mm~empty": "y",
    "empty~SDSSy_65mm": "y",
}

config.outfileBase = "FgcmLatissCalibrations"
# The default photometric survey so far uses g, r, i, z, y bands.
config.bands = ["g", "r", "i", "z", "y"]
config.fitBands = ["g", "r", "i", "z", "y"]
# This should be replaced with:
# from lsst.obs.lsst.filters import LATISS_FILTER_DEFINITIONS
# config.physicalFilterMap = LATISS_FILTER_DEFINITIONS.physical_to_band
# with TODO: DM-44705.
config.physicalFilterMap = physical_to_band
config.requiredBands = ["g", "r", "i"]

config.cycleNumber = 0
config.maxIterBeforeFinalCycle = 100
config.minCcdPerExp = 1
config.utBoundary = 0.0
config.washMjds = (0.0, )
# For now, define 1 observing epoch that encompasses everything.
config.epochMjds = (0.0, 100000.0)
config.coatingMjds = []
config.latitude = -30.2333
# This is pi*(1.2/2.)**2.
config.mirrorArea = 1.13097
config.defaultCameraOrientation = 0.0
config.brightObsGrayMax = 0.5
config.expGrayInitialCut = -0.5
config.expGrayPhotometricCutDict = {"g": -0.5, "r": -0.5, "i": -0.5, "z": -0.5, "y": -0.5}
config.expGrayHighCutDict = {"g": 0.2, "r": 0.2, "i": 0.2, "z": 0.2, "y": 0.2}
config.expVarGrayPhotometricCutDict = {"g": 0.1**2.,
                                       "r": 0.1**2.,
                                       "i": 0.1**2.,
                                       "z": 0.1**2.,
                                       "y": 0.1**2.}
config.autoPhotometricCutNSig = 3.0
config.autoHighCutNSig = 3.0
# Fit aperture corrections with only 2 bins to exercise the code.
config.aperCorrFitNBins = 0
config.aperCorrInputSlopeDict = {"g": 0.0,
                                 "r": 0.0,
                                 "i": 0.0,
                                 "z": 0.0,
                                 "y": 0.0}
# Define the band to SED constants approximately so they work
# for data that only has r, i observations.
config.sedboundaryterms = fgcmcal.SedboundarytermDict()
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
    "z": fgcmcal.Sedterm(primaryTerm="iz", secondaryTerm="zy", constant=1.0),
    "y": fgcmcal.Sedterm(primaryTerm="zy", secondaryTerm="iz", constant=0.25,
                         extrapolated=True, primaryBand="y", secondaryBand="z",
                         tertiaryBand="i"),
}

# Define good stars with an r-i color cut.
config.starColorCuts = ("g, i, 0.50, 3.5",)
config.refStarColorCuts = ("g, i, 0.6, 1.1",)
config.useExposureReferenceOffset = True
config.precomputeSuperStarInitialCycle = False
config.superStarSubCcdDict = {"g": True,
                              "r": True,
                              "i": True,
                              "z": True,
                              "y": True}
config.superStarPlotCcdResiduals = False
# Allow calibration to work with just 1 exposure on a night.
config.minExpPerNight = 10
# Allow calibration to work with very few stars per exposure.
config.minStarPerExp = 5
# Allow calibration to work with small number of stars in processing batches.
config.nStarPerRun = 500
config.nExpPerRun = 100
# Define r-i color as the primary way to split by color.
config.colorSplitBands = ["g", "i"]
config.freezeStdAtmosphere = True
# For tests, do low-order per-ccd polynomial.
config.superStarSubCcdChebyshevOrder = 2
config.ccdGraySubCcdDict = {"g": True,
                            "r": True,
                            "i": True,
                            "z": True,
                            "y": True}
config.ccdGrayFocalPlaneDict = {"g": False,
                                "r": False,
                                "i": False,
                                "z": False,
                                "y": False}
config.ccdGrayFocalPlaneFitMinCcd = 1
config.ccdGrayFocalPlaneChebyshevOrder = 1
# Do not model the magnitude errors (use errors as reported).
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
                                             "i": False,
                                             "z": False,
                                             "y": False}
config.sigFgcmMaxEGrayDict = {"g": 0.1,
                              "r": 0.1,
                              "i": 0.1,
                              "z": 0.1,
                              "y": 0.1}
config.approxThroughputDict = {"g": 1.0,
                               "r": 1.0,
                               "i": 1.0,
                               "z": 1.0,
                               "y": 1.0}

config.deltaAperFitPerCcdNx = 2
config.deltaAperFitPerCcdNy = 2
config.deltaAperInnerRadiusArcsec = 3.3493
config.deltaAperOuterRadiusArcsec = 4.78475
config.doComputeDeltaAperPerVisit = False
config.doComputeDeltaAperMap = False
config.doComputeDeltaAperPerCcd = False
