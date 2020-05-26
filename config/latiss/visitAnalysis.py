"""
LATISS-specific overrides for VisitAnalysisTask
"""
import os.path

obsConfigDir = os.path.dirname(__file__)

# Reference catalog
config.refObjLoader.load(os.path.join(obsConfigDir, 'gaiaFilterMap.py'))
config.refObjLoader.ref_dataset_name = "gaia_dr2_20200414"
