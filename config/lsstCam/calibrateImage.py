import os.path

from lsst.meas.algorithms import ColorLimit  # Configure the photometry to use the_monster.

config_dir = os.path.dirname(__file__)

config.connections.photometry_ref_cat = "the_monster_20250219"
config.connections.astrometry_ref_cat = "the_monster_20250219"

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

# Decrease maximum number of reference sources
config.astrometry.matcher.maxRefObjects = 4096

# Loosen maxOffset to account for early pointing model inaccuracy.
# NOTE: these only work for data post April 25, 2025, when the
#       LSSTCam pointing model was dramatically improved.  Data
#       taken before the update still require these to be ~1500 to
#       obtain good astrometric fits, and the following ticket is
#       to implement an acutal "fix" via the metadata-translator.
# TODO: DM-53164: Refit the pointing for LSSTCam observations prior
#       to April 25 and file metadata-patch tickets.
config.astrometry.matcher.maxOffsetPix = 500
config.astrometry_ref_loader.pixelMargin = 500

# Loosen minMatchDistanceArcSec, the match distance below which further
# iteration is pointless (arcsec) since we can only do as well as the
# camera model in SFM using the affine WCS fit.  (Having a larger value
# also gives poor seeing data a better chance of passing.)
# TODO: DM-47250. Tighten up (or remove) this override when an updated
# camera model is implemented.
config.astrometry.minMatchDistanceArcSec = 0.07

# Overrides to improved astrometry matching.
config.astrometry.doFiducialZeroPointCull = True
config.astrometry.load(os.path.join(config_dir, "fiducialZeroPoint.py"))

# Loosened for early LSSTCam with large PSFs.
config.photometry.match.sourceSelection.doUnresolved = False

# Turn on masking of diffraction spikes from bright stars.
config.doMaskDiffractionSpikes = True
