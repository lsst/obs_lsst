import os.path

from lsst.utils import getPackageDir

config.measurement.load(os.path.join(getPackageDir("obs_lsst"), "config", "apertures.py"))
config.measurement.load(os.path.join(getPackageDir("obs_lsst"), "config", "kron.py"))
config.load(os.path.join(getPackageDir("obs_lsst"), "config", "cmodel.py"))

config.measurement.slots.gaussianFlux = None
