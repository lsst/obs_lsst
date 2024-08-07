import os

from lsst.meas.algorithms import ColorLimit  # Configure the photometry to use atlas_refcat2.

# Configure the photometry to use atlas_refcat2.
config_dir = os.path.dirname(__file__)

config.connections.photometry_ref_cat = "atlas_refcat2_20220201"
config.photometry_ref_loader.load(os.path.join(config_dir, "filterMap.py"))

config.photometry.match.referenceSelection.magLimit.fluxField = "r_flux"
colors = config.photometry.match.referenceSelection.colorLimits
colors["g-r"] = ColorLimit(primary="g_flux", secondary="r_flux", minimum=0.4, maximum=2.0)

config.photometry.applyColorTerms = True
config.photometry.photoCatName = "atlas_refcat2_20220201"
config.photometry.colorterms.load(os.path.join(config_dir, "colorterms.py"))

config.compute_summary_stats.load(os.path.join(config_dir, "computeExposureSummaryStats.py"))
