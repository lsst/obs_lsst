import os

from lsst.meas.algorithms import ColorLimit  # Configure the photometry to use the_monster.

# Configure the photometry to use atlas_refcat2.
config_dir = os.path.dirname(__file__)

config.connections.photometry_ref_cat = "the_monster_20250219"
config.connections.astrometry_ref_cat = "the_monster_20250219"

# Turn on illumination corrections.
config.do_illumination_correction = True
config.psf_subtract_background.doApplyFlatBackgroundRatio = True
config.psf_detection.doApplyFlatBackgroundRatio = True
config.star_background.doApplyFlatBackgroundRatio = True
config.star_detection.doApplyFlatBackgroundRatio = True

config.astrometry.load(os.path.join(config_dir, "filterMap.py"))
config.photometry_ref_loader.load(os.path.join(config_dir, "filterMap.py"))

config.photometry.match.referenceSelection.magLimit.fluxField = "monster_ComCam_r_flux"
colors = config.photometry.match.referenceSelection.colorLimits
colors["g-r"] = ColorLimit(
    primary="monster_ComCam_g_flux",
    secondary="monster_ComCam_r_flux",
    minimum=0.4,
    maximum=2.0
)

config.photometry.applyColorTerms = False
config.photometry.photoCatName = "the_monster_20250219"

config.compute_summary_stats.load(os.path.join(config_dir, "computeExposureSummaryStats.py"))

# Loosen maxOffset to account for early pointing model inaccuracy.
config.astrometry.matcher.maxOffsetPix=1500
config.astrometry_ref_loader.pixelMargin=1500

# Loosen minMatchDistanceArcSec, the match distance below which further
# iteration is pointless (arcsec) since we can only do as well as the
# camera model in SFM using the affine WCS fit.
# TODO: DM-47250. Tighten up (or remove) this override when an updated
# camera model is implemented.
config.astrometry.minMatchDistanceArcSec = 0.04

# Overrides to improved astrometry matching.
config.astrometry.doFiducialZeroPointCull = True
config.astrometry.load(os.path.join(config_dir, "fiducialZeroPoint.py"))

# Loosened for early ComCam with large PSFs.
config.photometry.match.sourceSelection.doUnresolved = False

# Turn on masking of diffraction spikes from bright stars.
config.doMaskDiffractionSpikes = True
