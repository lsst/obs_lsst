"""
LSST Cam-specific overrides for CoaddAnalysisTask
"""
import os.path

from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask

# Reference catalog
config.astromRefObjLoader.load(os.path.join(os.path.dirname(__file__), "filterMap.py"))
config.photomRefObjLoader.load(os.path.join(os.path.dirname(__file__), "filterMap.py"))
config.astromRefObjLoader.ref_dataset_name="cal_ref_cat"
config.photomRefObjLoader.ref_dataset_name="cal_ref_cat"
config.astromRefCat="cal_ref_cat"
config.photomRefCat="cal_ref_cat"

config.doWriteParquetTables=False
config.doApplyColorTerms=False
