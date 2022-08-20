from lsst.meas.astrom import FitAffineWcsTask

# Configure the photometry to use atlas_refcat2.
config.connections.photoRefCat = 'atlas_refcat2_20220201'
config.photoCal.match.referenceSelection.magLimit.fluxField = "r_flux"

# We often have very few sources due to smaller aperture so use affine task. 
config.astrometry.wcsFitter.retarget(FitAffineWcsTask)

# Increase maxoffset as AUXTEL pointing can be unreliable. Between Feb2020-Mar2022 we saw offsets
# of up to 4 arcmin, which translates to 2400pix. We choose 3000 as a conservative limit. pixelMargin 
# also increased to ensure refcat overlap when we see large pointing offsets considering a 3000pix 
# offset and detector half-width of 2100pix. 
config.astromRefObjLoader.pixelMargin = 900
config.astrometry.matcher.maxOffsetPix = 3000

# Apply a magnitude limit and decrease the SNR limit as we're only a 1.2m
# and frequently take short exposures. Also, allow max rotation while the
# instrumental repeatability isn't good.
config.astrometry.referenceSelector.doMagLimit = True
config.astrometry.referenceSelector.magLimit.minimum = 1
config.astrometry.referenceSelector.magLimit.maximum = 18
config.astrometry.referenceSelector.magLimit.fluxField = "phot_g_mean_flux"
config.astrometry.matcher.maxRotationDeg = 5.99
config.astrometry.sourceSelector['matcher'].minSnr = 10

# Write srcMatchFull
config.doWriteMatchesDenormalized = True
