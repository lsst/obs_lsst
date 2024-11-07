import os

from lsst.meas.algorithms import ColorLimit  # Configure the photometry to use the_monster.

# Configure the photometry to use atlas_refcat2.
config_dir = os.path.dirname(__file__)

config.connections.photometry_ref_cat = "the_monster_20240904"
config.photometry_ref_loader.load(os.path.join(config_dir, "filterMap.py"))

config.photometry.match.referenceSelection.magLimit.fluxField = "monster_SynthLSST_r_flux"
colors = config.photometry.match.referenceSelection.colorLimits
colors["g-r"] = ColorLimit(
    primary="monster_SynthLSST_g_flux",
    secondary="monster_SynthLSST_r_flux",
    minimum=0.4,
    maximum=2.0
)


config.photometry.applyColorTerms = False
config.photometry.photoCatName = "the_monster_20240904"

config.compute_summary_stats.load(os.path.join(config_dir, "computeExposureSummaryStats.py"))

# Loosen maxOffset to account for early pointing model inaccuracy.
config.astrometry.matcher.maxOffsetPix=1500
config.astrometry_ref_loader.pixelMargin=1500

# Loosened for early ComCam with large PSFs.
config.photometry.match.sourceSelection.doUnresolved = False
