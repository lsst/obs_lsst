import os

physical_to_band = {
    "g_01": "g",
    "r_03": "r",
    "i_06": "i",
}

config.requiredBands = []
config.primaryBands = ["i", "r", "g"]

config.coarseNside = 64

config.minPerBand = 2
config.connections.ref_cat = "uw_stars_20240524"

configDir = os.path.join(os.path.dirname(__file__))
config.physicalFilterMap = physical_to_band
config.fgcmLoadReferenceCatalog.filterMap = {
    "g": "lsst_g",
    "r": "lsst_r",
    "i": "lsst_i",
    "g_01": "lsst_g",
    "r_03": "lsst_r",
    "i_06": "lsst_i",
}
config.fgcmLoadReferenceCatalog.applyColorTerms = False
config.fgcmLoadReferenceCatalog.referenceSelector.doSignalToNoise = True
config.fgcmLoadReferenceCatalog.referenceSelector.signalToNoise.fluxField = "lsst_i_flux"
config.fgcmLoadReferenceCatalog.referenceSelector.signalToNoise.errField = "lsst_i_fluxErr"
config.fgcmLoadReferenceCatalog.referenceSelector.signalToNoise.minimum = 50.0
