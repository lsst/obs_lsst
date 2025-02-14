# DM-48093: Order 2 does not looks to be enough
# for spatial interpolation of the PSF. Order 4
# remove most of spatial structure.
config.psf_determiner['piff'].spatialOrder = 4
# See DM-48887 for more detail.
config.psf_determiner['piff'].zerothOrderInterpNotEnoughStars = True
