"""
LSST Cam-specific overrides for VisitAnalysisTask
"""
import os.path

from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask

# Reference catalog
config.astromRefObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.photomRefObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.astromRefObjLoader.load(os.path.join(os.path.dirname(__file__), "filterMap.py"))
config.photomRefObjLoader.load(os.path.join(os.path.dirname(__file__), "filterMap.py"))
config.astromRefObjLoader.ref_dataset_name = "cal_ref_cat"
config.photomRefObjLoader.ref_dataset_name = "cal_ref_cat"
config.astromRefCat = "cal_ref_cat"
config.photomRefCat = "cal_ref_cat"

config.doApplyExternalPhotoCalib = False
config.doApplyExternalSkyWcs = False
config.doApplyColorTerms = False
config.doWriteParquetTables = False
