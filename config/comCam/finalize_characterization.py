# DM-48093: Order 2 does not looks to be enough
# for spatial interpolation of the PSF. Order 4
# remove most of spatial structure.
# See DM-49673 for u-band.
config.psf_determiner['piff'].spatialOrderPerBand = {
    "u": 2,
    "g": 4,
    "r": 4,
    "i": 4,
    "z": 4,
    "y": 4,
}
# See DM-48887 & DM-49688 for more detail.
config.psf_determiner['piff'].zerothOrderInterpNotEnoughStars = False
# See DM-49152 for more detail.
config.psf_determiner['piff'].piffBasisPolynomialSolver = "cpp"
config.psf_determiner['piff'].piffPixelGridFitCenter = False
# See DM-45569, but this is not enable but it was the config
# used in the plots.
config.psf_determiner['piff'].useColor = False
config.psf_determiner['piff'].colorOrder = 1
config.psf_determiner['piff'].color = {
    "u": "g-i",
    "g": "g-i",
    "r": "g-i",
    "i": "g-i",
    "z": "g-i",
    "y": "g-i",
}
