import os.path

from lsst.meas.algorithms import ColorLimit
config_dir = os.path.dirname(__file__)

# Configure the photometry to use the Monster correctly.
config.photometry_ref_loader.load(os.path.join(config_dir, "filterMap.py"))

config.photometry.match.referenceSelection.magLimit.fluxField = "r_flux"
colors = config.photometry.match.referenceSelection.colorLimits
colors["g-r"] = ColorLimit(primary="g_flux", secondary="r_flux", minimum=0.4, maximum=2.0)

config.compute_summary_stats.load(os.path.join(config_dir, "computeExposureSummaryStats.py"))
