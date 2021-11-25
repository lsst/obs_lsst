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

# keep these
config.measurePsf.psfDeterminer = 'pca'
config.measurePsf.psfDeterminer['pca'].spatialOrder = 0
config.measurePsf.starSelector['objectSize'].fluxMin = 12500./5
config.installSimplePsf.width = 81  # why is the default 11?!
config.installSimplePsf.fwhm = 2.355*2

# playground
# config.measurePsf.psfDeterminer['pca'].tolerance = 0
# config.measurePsf.psfDeterminer['pca'].reducedChi2ForPsfCandidates = 0

config.measurePsf.psfDeterminer['pca'].sizeCellX = 4100
config.measurePsf.psfDeterminer['pca'].sizeCellY = 4100

# Apparently pointless
# config.measurePsf.starSelector['objectSize'].widthMax = 40.
# config.measurePsf.starSelector['objectSize'].widthStdAllowed = .5
# config.measurePsf.starSelector['objectSize'].nSigmaClip = 3
