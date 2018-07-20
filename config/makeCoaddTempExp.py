import os.path
from lsst.utils import getPackageDir

# Load configs shared between assembleCoadd and makeCoaddTempExp
config.load(os.path.join(getPackageDir("obs_lsstCam"), "config", "coaddBase.py"))

config.makePsfMatched = True
config.warpAndPsfMatch.psfMatch.kernel['AL'].alardSigGauss = [1.0, 2.0, 4.5]
config.modelPsf.defaultFwhm = 7.7

# To be uncommented when we will run jointcal
#config.doApplyUberCal = True

# To be uncommented when we will have sky background estimates
#config.doApplySkyCorr = True
