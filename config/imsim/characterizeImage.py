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

config.load(os.path.join(obsConfigDir, "..", "cmodel.py"))
config.measurement.load(os.path.join(obsConfigDir, "..", "kron.py"))
config.measurement.load(os.path.join(obsConfigDir, "..", "convolvedFluxes.py"))
config.measurement.load(os.path.join(obsConfigDir, "..", "gaap.py"))
config.measurement.load(os.path.join(obsConfigDir, "..", "hsm.py"))

if "ext_shapeHSM_HsmShapeRegauss" in config.measurement.plugins:
    # no deblending has been done
    config.measurement.plugins["ext_shapeHSM_HsmShapeRegauss"].deblendNChild = ""

# Convolved fluxes can fail for small target seeing if the observation seeing is larger
if "ext_convolved_ConvolvedFlux" in config.measurement.plugins:
    names = config.measurement.plugins["ext_convolved_ConvolvedFlux"].getAllResultNames()
    config.measureApCorr.allowFailure += names

if "ext_gaap_GaapFlux" in config.measurement.plugins:
    names = config.measurement.plugins["ext_gaap_GaapFlux"].getAllGaapResultNames()
    config.measureApCorr.allowFailure += names

# Reduce Chebyshev polynomial order for background fitting (DM-30820);
# imsim has a constant offset background.
config.background.approxOrderX = 1
config.detection.background.approxOrderX = 1
config.detection.tempLocalBackground.approxOrderX = 1
config.detection.tempWideBackground.approxOrderX = 1
config.repair.cosmicray.background.approxOrderX = 1

# S/N cuts for computing aperture corrections to include only objects that
# were used in the PSF model and have PSF flux S/N greater than the minimum
# set (DM-23071).
config.measureApCorr.sourceSelector["science"].signalToNoise.minimum = 150.0
