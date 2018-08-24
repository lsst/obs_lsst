import os.path

from lsst.utils import getPackageDir

config.measurement.load(os.path.join(getPackageDir("obs_lsstCam"), "config", "apertures.py"))
config.measurement.load(os.path.join(getPackageDir("obs_lsstCam"), "config", "kron.py"))
config.load(os.path.join(getPackageDir("obs_lsstCam"), "config", "cmodel.py"))

config.measurement.slots.instFlux = None
