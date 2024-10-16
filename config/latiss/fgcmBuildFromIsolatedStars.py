import os
from lsst.obs.lsst.filters import LATISS_FILTER_DEFINITIONS


config.requiredBands = []
config.primaryBands = ["i", "r", "g", "z", "y"]

config.coarseNside = 64

config.minPerBand = 2
config.connections.ref_cat = "the_monster_20240904"

config.apertureInnerInstFluxField = "apFlux_35_0_instFlux"
config.apertureOuterInstFluxField = "apFlux_50_0_instFlux"

configDir = os.path.join(os.path.dirname(__file__))
config.physicalFilterMap = LATISS_FILTER_DEFINITIONS.physical_to_band
config.doSubtractLocalBackground = False
config.fgcmLoadReferenceCatalog.load(os.path.join(configDir, "filterMap.py"))
config.fgcmLoadReferenceCatalog.applyColorTerms = True
config.fgcmLoadReferenceCatalog.colorterms.load(os.path.join(configDir, "colorterms.py"))
config.fgcmLoadReferenceCatalog.referenceSelector.doSignalToNoise = True
config.fgcmLoadReferenceCatalog.referenceSelector.signalToNoise.fluxField = "i_flux"
config.fgcmLoadReferenceCatalog.referenceSelector.signalToNoise.errField = "i_fluxErr"
config.fgcmLoadReferenceCatalog.referenceSelector.signalToNoise.minimum = 50.0
