from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask

REFCAT_NAME = 'gaia'
# REFCAT_NAME = 'ps1'

if REFCAT_NAME == 'gaia':
    REFCAT = "gaia_dr2_20200414"
else:
    REFCAT = "ps1_pv3_3pi_20170110"

config.refObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.refObjLoader.ref_dataset_name = REFCAT

config.doDeblend = False
