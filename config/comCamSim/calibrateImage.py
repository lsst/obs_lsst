# ComCamSim-specialized configuration for CalibrateImageTask.
import os.path

configDir = os.path.dirname(__file__)

config.connections.astrometry_ref_cat = "uw_stars_20240228"
config.connections.photometry_ref_cat = "uw_stars_20240228"

config.astrometry_ref_loader.load(os.path.join(configDir, "filterMap.py"))
config.photometry_ref_loader.load(os.path.join(configDir, "filterMap.py"))
config.astrometry_ref_loader.anyFilterMapsToThis = None
config.photometry_ref_loader.anyFilterMapsToThis = None
