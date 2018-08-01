import os.path

from lsst.utils import getPackageDir
# The following will have to be uncommented and adapted when the
# X-talk correction will be active
#from lsst.obs.lsstCam.isr import SubaruIsrTask
#config.isr.retarget(SubaruIsrTask)
#config.isr.load(os.path.join(getPackageDir("obs_lsstCam"), "config", "isr.py"))

config.load(os.path.join(getPackageDir("obs_lsstCam"), "config", "lsstCam.py"))

configDir = os.path.join(getPackageDir("obs_lsstCam"), "config")
bgFile = os.path.join(configDir, "background.py")
fpBgFile = os.path.join(configDir, "focalPlaneBackground.py")

config.largeScaleBackground.load(fpBgFile)
config.detection.background.load(bgFile)
config.subtractBackground.load(bgFile)

config.isr.doBrighterFatter = False
