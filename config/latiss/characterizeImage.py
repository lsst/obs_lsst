from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask

# Switch to PCA determiner as it is much more robust when there are very few
# sources. Increase default FWHM due to plate scale and reduce fluxMin due to
# short expTimes on a 1.2m telescope. nEigenComponents and spatialOrder set to
# min values so that we always succeed even with one or two stars.
config.measurePsf.psfDeterminer = 'pca'
config.measurePsf.psfDeterminer['pca'].spatialOrder = 0
config.measurePsf.psfDeterminer['pca'].nEigenComponents = 1
config.measurePsf.starSelector['objectSize'].fluxMin = 2500
config.installSimplePsf.width = 81  
config.installSimplePsf.fwhm = 2.355*2 # LATISS platescale is 2x LSST nominal
