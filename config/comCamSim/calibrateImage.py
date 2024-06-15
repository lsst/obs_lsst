# ComCamSim-specialized configuration for CalibrateImageTask.
import os.path

configDir = os.path.dirname(__file__)

config.connections.astrometry_ref_cat = "uw_stars_20240228"
config.connections.photometry_ref_cat = "uw_stars_20240228"

config.astrometry_ref_loader.load(os.path.join(configDir, "filterMap.py"))
config.photometry_ref_loader.load(os.path.join(configDir, "filterMap.py"))
config.astrometry_ref_loader.anyFilterMapsToThis = None
config.photometry_ref_loader.anyFilterMapsToThis = None

# The following magnitude limits for reference objects used in the
# astrometric and photometric calibrations were selected to more than
# span the expected magnitude range of the science sources available
# for the calibrations (see DM-43143 for example distributions).  This
# is to avoid passing reference objects to the matcher that sould not
# be in contention for matching (thus reducing the chance of locking
# onto a bad match).
# TODO: remove (or update) once DM-43168 is implemented.
config.astrometry.referenceSelector.doMagLimit = True
config.astrometry.referenceSelector.magLimit.fluxField = "lsst_r_flux"
config.astrometry.referenceSelector.magLimit.minimum = 14.0
config.astrometry.referenceSelector.magLimit.maximum = 22.0

config.photometry.match.referenceSelection.doMagLimit = True
config.photometry.match.referenceSelection.magLimit.fluxField = "lsst_r_flux"
config.photometry.match.referenceSelection.magLimit.minimum = 14.0
config.photometry.match.referenceSelection.magLimit.maximum = 22.0

# Exposure summary stats
config.compute_summary_stats.load(os.path.join(configDir, "computeExposureSummaryStats.py"))
