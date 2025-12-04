"""LSSTCam-specific overrides for MakePsfMatchedWarpTask"""

# Set to 1.8 arcsec FWHM, and match the selection cut in SelectImagesTask
config.modelPsf.defaultFwhm = 9.0
# Increase kernel size to handle larger PSFs
config.psfMatch.kernel['AL'].kernelSize = 41
