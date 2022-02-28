from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask

# support multiple refacts with configuration at a single point here,
# with logic following to allow easy switching between Gaia and Pan-STARRS
REFCAT_NAME = 'gaia'
# REFCAT_NAME = 'ps1'

if REFCAT_NAME == 'gaia':
    REFCAT = "gaia_dr2_20200414"
else:
    REFCAT = "ps1_pv3_3pi_20170110"

config.refObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.refObjLoader.ref_dataset_name = REFCAT

# we are at the other end of the regime
config.doDeblend = False

# switch to PCA determiner as it is much more robust when there are very few
# sources. Increase default FWHM due to plate scale and reduce fluxMin due to
# short expTimes on a 1.2m telescope. nEigenComponents and spatialOrder set to
# min values so that we always succeed even with one or two stars.
config.measurePsf.psfDeterminer = 'pca'
config.measurePsf.psfDeterminer['pca'].spatialOrder = 0
config.measurePsf.psfDeterminer['pca'].nEigenComponents = 1
config.measurePsf.starSelector['objectSize'].fluxMin = 2500
config.installSimplePsf.width = 81  # why is the default 11?!
config.installSimplePsf.fwhm = 2.355*2
