"""
ImSim-specific overrides for CalibrateImageTask
"""
import os

config_dir = os.path.join(os.path.dirname(__file__))

# imsim background model is a single value per detector.
config.psf_detection.background.approxOrderX: 1
config.psf_detection.tempLocalBackground.approxOrderX: 1
config.psf_detection.tempWideBackground.approxOrderX: 1
config.psf_repair.cosmicray.background.approxOrderX: 1
config.star_detection.background.approxOrderX = 1
config.star_detection.tempLocalBackground.approxOrderX = 1
config.star_detection.tempWideBackground.approxOrderX = 1

# imSim-specifc reference catalogs
config.connections.astrometry_ref_cat = "cal_ref_cat_2_2"
config.connections.photometry_ref_cat = "cal_ref_cat_2_2"
# Use the ImSim filterMap ("lsst_X_smeared" reference fluxes).
config.astrometry_ref_loader.load(os.path.join(config_dir, 'filterMap.py'))
config.astrometry_ref_loader.anyFilterMapsToThis = None
config.photometry_ref_loader.load(os.path.join(config_dir, 'filterMap.py'))

# Make sure galaxies from truth catalog are not used for calibration.
config.astrometry.referenceSelector.doUnresolved = True
config.astrometry.referenceSelector.unresolved.name = "resolved"
config.astrometry.referenceSelector.unresolved.minimum = None
config.astrometry.referenceSelector.unresolved.maximum = 0.5
config.photometry.match.referenceSelection.doUnresolved = True
config.photometry.match.referenceSelection.unresolved.name = "resolved"
config.photometry.match.referenceSelection.unresolved.minimum = None
config.photometry.match.referenceSelection.unresolved.maximum = 0.5

# Only use brighter sources from the very deep truth catalog.
config.photometry.match.referenceSelection.doMagLimit = True
config.photometry.match.referenceSelection.magLimit.fluxField = "lsst_i_smeared_flux"
config.photometry.match.referenceSelection.magLimit.maximum = 22.0
