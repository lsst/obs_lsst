import os

physical_to_band = {
    "u_02": "u",
    "g_01": "g",
    "r_03": "r",
    "i_06": "i",
    "z_03": "z",
    "y_04": "y",
}

config.requiredBands = []
config.primaryBands = ["i", "r", "g", "z", "y", "u"]

config.coarseNside = 64

config.minPerBand = 2
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

config.doApplyWcsJacobian = False
