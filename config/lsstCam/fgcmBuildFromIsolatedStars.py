import os

physical_to_band = {
    "u_26": "u",
    "g_6": "g",
    "r_57": "r",
    "i_39": "i",
    "z_20": "z",
    "y_10": "y",
}

config.requiredBands = []
config.primaryBands = ["i", "r", "g", "z", "y", "u"]

config.coarseNside = 64

config.connections.ref_cat = "the_monster_20250219"

configDir = os.path.join(os.path.dirname(__file__))
config.physicalFilterMap = physical_to_band
obsConfigDir = os.path.join(os.path.dirname(__file__))
config.fgcmLoadReferenceCatalog.load(os.path.join(obsConfigDir, "filterMap.py"))
config.fgcmLoadReferenceCatalog.applyColorTerms = False
config.fgcmLoadReferenceCatalog.referenceSelector.doSignalToNoise = True
config.fgcmLoadReferenceCatalog.referenceSelector.signalToNoise.fluxField = "monster_ComCam_i_flux"
config.fgcmLoadReferenceCatalog.referenceSelector.signalToNoise.errField = "monster_ComCam_i_fluxErr"
config.fgcmLoadReferenceCatalog.referenceSelector.signalToNoise.minimum = 50.0

# Temporary until we turn on illumination corrections.
config.doApplyWcsJacobian = True
