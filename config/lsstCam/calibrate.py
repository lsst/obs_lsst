from lsst.meas.algorithms import ColorLimit  # Configure the photometry to use the_monster.

config.photoRefObjLoader.load("filterMap.py")
config.connections.astromRefCat = "the_monster_20250219"
# photometric reference catalog defaults to the_monster_20250219 one level up
# photoCal.applyColorTerms = False one level up


config.photoCal.match.referenceSelection.magLimit.fluxField = "monster_ComCam_r_flux"
colors = config.photoCal.match.referenceSelection.colorLimits
colors["g-r"] = ColorLimit(
    primary="monster_ComCam_g_flux",
    secondary="monster_ComCam_r_flux",
    minimum=0.4,
    maximum=2.0
)

# Loosen maxOffset to account for early pointing model inaccuracy.
config.astrometry.matcher.maxOffsetPix=1500
config.astromRefObjLoader.pixelMargin=1500

# TODO: DM-47250. Tighten up (or remove) this override when an updated
# camera model is implemented.
config.astrometry.minMatchDistanceArcSec = 0.04

# Overrides to improved astrometry matching.
config.astrometry.doFiducialZeroPointCull = True
config.astrometry.load("fiducialZeroPoint.py")

# Loosened for early ComCam with large PSFs.
config.photoCal.match.sourceSelection.doUnresolved = False

# Exposure summary stats.
config.computeSummaryStats.load("computeExposureSummaryStats.py")
