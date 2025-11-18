"""
lsstCam-specific overrides for assembleCellCoadd
"""

# Need to reject VIGNETTED pixels, but VIGNETTED pixels also have NO_DATA set,
# and NO_DATA is in default bad_mask_planes.
config.bad_mask_planes += ["PARTLY_VIGNETTED"]
config.bad_mask_planes += ["SPIKE"]

# Number of Monte-Carlo noise realizations to coadd.
# This must be equal to or lesser than the numberOfNoiseRealizations
# value in makeDirectWarp.
config.num_noise_realizations = 1

# Set the dimensions of the PSF image.
config.psf_dimensions = 35

# Generate edgeless cell coadds (at least for DP2).
config.min_overlap_fraction = 1.0
