# Change the PSF determiner to psfex from piff default as the latter will not
# scale well to the large kernel/stamp sizes for PSF modeling for LATISS data.
import lsst.meas.extensions.psfex.psfexPsfDeterminer  # noqa: F401 required to use psfex below

config.psf_determiner.name = "psfex"
# Reduce spatialOrder to 1, this helps ensure success with low numbers of psf candidates.
config.psf_determiner["psfex"].spatialOrder = 1
# Set the default kernel and stamp sizes for PSF modeling appropriate for LATISS.
config.psf_determiner["psfex"].stampSize = 71
config.make_psf_candidates.kernelSize = 71

config.source_selector["science"].signalToNoise.minimum = 20.0
