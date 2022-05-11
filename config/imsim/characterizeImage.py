# This file is part of obs_lsst.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
"""
imsim-specific overrides for CharacterizeImageTask
"""

import os.path

obsConfigDir = os.path.join(os.path.dirname(__file__))

# Astrometry refcat overrides for simulations
config.refObjLoader.load(os.path.join(obsConfigDir, 'filterMap.py'))
config.refObjLoader.ref_dataset_name = 'cal_ref_cat'

# Reduce Chebyshev polynomial order for background fitting (DM-30820)
config.background.approxOrderX = 1
config.detection.background.approxOrderX = 1
config.detection.tempLocalBackground.approxOrderX = 1
config.detection.tempWideBackground.approxOrderX = 1
config.repair.cosmicray.background.approxOrderX = 1

# Select candidates for PSF modeling based on S/N threshold (DM-17043 & DM-16785)
config.measurePsf.starSelector["objectSize"].doFluxLimit = False
config.measurePsf.starSelector["objectSize"].doSignalToNoiseLimit = True

# S/N cuts for computing aperture corrections to include only objects that
# were used in the PSF model and have PSF flux S/N greater than the minimum
# set (DM-23071).
config.measureApCorr.sourceSelector["science"].doFlags = True
config.measureApCorr.sourceSelector["science"].doSignalToNoise = True
config.measureApCorr.sourceSelector["science"].flags.good = ["calib_psf_used"]
config.measureApCorr.sourceSelector["science"].flags.bad = []
config.measureApCorr.sourceSelector["science"].signalToNoise.minimum = 150.0
config.measureApCorr.sourceSelector.name = "science"

# enable the full suite of measurements
config.load(os.path.join(obsConfigDir, "cmodel.py"))
config.measurement.load(os.path.join(obsConfigDir, "kron.py"))
config.measurement.load(os.path.join(obsConfigDir, "convolvedFluxes.py"))
config.measurement.load(os.path.join(obsConfigDir, "gaap.py"))
