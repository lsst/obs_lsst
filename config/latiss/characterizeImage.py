# To ensure as many candidates as possible are passed to measurePsf, we use a simple 'science' star selector, 
# including only a signal to noise limit and pixel flag filter to filter out bad candidates. THe SNR>30 limit
# corresponds to a band-dependent magnitude of around 19 on LATISS in a 30s image, so galaxy contamination is 
# limited. The default objectSize star selector is not appropriate given the low number of sources and 
# PSF variations across the FOV. 
config.measurePsf.starSelector = 'science'
config.measurePsf.starSelector['science'].doSignalToNoise = True
config.measurePsf.starSelector['science'].signalToNoise.minimum = 30.0
config.measurePsf.starSelector['science'].signalToNoise.maximum = None
config.measurePsf.starSelector['science'].signalToNoise.fluxField = "base_GaussianFlux_instFlux"
config.measurePsf.starSelector['science'].signalToNoise.errField = "base_GaussianFlux_instFluxErr"
config.measurePsf.starSelector['science'].doFlags = True
config.measurePsf.starSelector['science'].flags.bad = ["base_PixelFlags_flag_edge",
                        "base_PixelFlags_flag_interpolatedCenter",
                        "base_PixelFlags_flag_saturatedCenter",
                        "base_PixelFlags_flag_crCenter",
                        "base_PixelFlags_flag_bad",
                        "base_PixelFlags_flag_interpolated"]

# We are starved for PSF stars, so don't reserve any at this stage.
config.measurePsf.reserve.fraction = 0.0

# Use these to run the pca psf estimator 
#config.measurePsf.psfDeterminer = 'pca'
#config.measurePsf.psfDeterminer['pca'].spatialOrder = 0

# Reduce psfex spatialOrder to 1, this helps ensure success with low numbers of psf candidates.
config.measurePsf.psfDeterminer['psfex'].spatialOrder = 1

config.installSimplePsf.width = 81  
config.installSimplePsf.fwhm = 2.355*2 # LATISS platescale is 2x LSST nominal
