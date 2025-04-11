# PFL recommends starting with spatial order 2
config.psf_determiner['piff'].spatialOrderPerBand = {
    "u": 2,
    "g": 2,
    "r": 2,
    "i": 2,
    "z": 2,
    "y": 2,
}
# See DM-48887 & DM-49688 for more detail.
config.psf_determiner['piff'].zerothOrderInterpNotEnoughStars = False
# See DM-49152 for more detail.
config.psf_determiner['piff'].piffBasisPolynomialSolver = "cpp"
config.psf_determiner['piff'].piffPixelGridFitCenter = False
