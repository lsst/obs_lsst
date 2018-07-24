import os.path
from lsst.utils import getPackageDir

# Load configs shared between assembleCoadd and makeCoaddTempExp
config.load(os.path.join(getPackageDir("obs_lsstCam"), "config", "coaddBase.py"))

config.makePsfMatched = True
config.warpAndPsfMatch.psfMatch.kernel['AL'].alardSigGauss = [1.0, 2.0, 4.5]
config.modelPsf.defaultFwhm = 7.7

# FUTURE: Set to True when we decide to run jointcal
config.doApplyUberCal = False

# FUTURE: Set to True when we have sky background estimate
config.doApplySkyCorr = False
