# https://rubinobs.atlassian.net/browse/DM-53160 for DP2.
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
